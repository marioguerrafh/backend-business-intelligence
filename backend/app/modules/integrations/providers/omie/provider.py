from __future__ import annotations

import json
import logging
import re
import time
from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from app.modules.integrations.application.provider_interface import (
    ProviderAuthResult,
    ProviderSyncResult,
    TemplateSyncResult,
)
from app.modules.integrations.infrastructure.ingest_gateway import IntegrationIngestGateway
from app.modules.integrations.providers.omie import mappers
from app.modules.integrations.providers.omie.config import load_omie_provider_config
from app.modules.integrations.providers.omie.runtime import OmieRuntime
from app.modules.integrations.providers.shared.resilience import (
    CircuitBreaker,
    RateLimiter,
    RetryPolicy,
    RetryableProviderError,
    resilient_call,
)


@dataclass(slots=True)
class OmieProvider:
    ingest_gateway: IntegrationIngestGateway
    retry_policy: RetryPolicy
    rate_limiter: RateLimiter
    circuit_breaker: CircuitBreaker
    runtime: OmieRuntime | None = None
    provider_type: str = "omie"
    _logger: ClassVar[logging.Logger] = logging.getLogger("app.integrations.omie")

    _DEFAULT_BASE_URL: ClassVar[str] = "https://app.omie.com.br/api/v1/"
    _DEFAULT_ENDPOINTS: ClassVar[dict[str, dict[str, Any]]] = {
        "customers": {
            "path": "geral/clientes/",
            "call": "ListarClientes",
            "list_path": "clientes_cadastro",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "products": {
            "path": "geral/produtos/",
            "call": "ListarProdutos",
            "list_path": "produto_servico_cadastro",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "sales": {
            "path": "produtos/pedido/",
            "call": "ListarPedidos",
            "list_path": "pedido_venda_produto",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "accounts_receivable": {
            "path": "financas/contareceber/",
            "call": "ListarContasReceber",
            "list_path": "conta_receber_cadastro",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "accounts_payable": {
            "path": "financas/contapagar/",
            "call": "ListarContasPagar",
            "list_path": "conta_pagar_cadastro",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "cashflow": {
            "path": "financas/extrato/",
            "call": "ListarExtrato",
            "list_path": "movimento",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "inventory": {
            "path": "estoque/consulta/",
            "call": "ListarPosicoes",
            "list_path": "produto",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
        "hr": {
            "path": "folha/resumo/",
            "call": "ListarResumoFolha",
            "list_path": "resumo",
            "page_field": "pagina",
            "page_size_field": "registros_por_pagina",
            "page_size": 100,
        },
    }

    def __post_init__(self) -> None:
        if self.runtime is None:
            self.runtime = OmieRuntime(load_omie_provider_config())

    def authenticate(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderAuthResult:
        app_key = str(credentials.get("app_key") or "").strip()
        app_secret = str(credentials.get("app_secret") or "").strip()
        if not app_key or not app_secret:
            raise ValueError("omie credentials require app_key and app_secret")
        return ProviderAuthResult(connected=True, external_account_id=f"omie:{company_id}:{app_key[:4]}")

    def health(self, *, company_id: str, credentials: dict[str, Any]) -> dict[str, Any]:
        self.authenticate(company_id=company_id, credentials=credentials)
        assert self.runtime is not None
        circuit = self.circuit_breaker.snapshot()
        runtime_snapshot = self.runtime.health_snapshot()
        status = "degraded" if circuit.get("state") in {"open", "half_open"} else "ok"
        return {
            "provider": "omie",
            "status": status,
            "queue": runtime_snapshot.get("queue", {}),
            "cache_size": runtime_snapshot.get("cache_size", 0),
            "circuit_breaker": circuit,
            "metrics": runtime_snapshot.get("metrics", {}),
        }

    def sync_customers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="customers", mode=mode)
        mapped = [mappers.map_customer(item) for item in raw]
        result = self.ingest_gateway.ingest_customers(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_products(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="products", mode=mode)
        mapped = [mappers.map_product(item) for item in raw]
        result = self.ingest_gateway.ingest_products(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_suppliers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        # Supplier aggregate is represented through accounts payable in canonical financial layer.
        return TemplateSyncResult(
            template="suppliers",
            records_read=0,
            records_imported=0,
            records_failed=0,
            import_job_id=None,
            ingest_event_id=None,
            pipeline_run_id=None,
        )

    def sync_sales(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="sales", mode=mode)
        period_ref = self._period_ref(credentials)
        mapped = [mappers.map_sale(item, period_ref=period_ref) for item in raw]
        result = self.ingest_gateway.ingest_sales(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_accounts_receivable(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="accounts_receivable", mode=mode)
        period_ref = self._period_ref(credentials)
        mapped = [mappers.map_accounts_receivable(item, period_ref=period_ref) for item in raw]
        result = self.ingest_gateway.ingest_accounts_receivable(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_accounts_payable(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="accounts_payable", mode=mode)
        period_ref = self._period_ref(credentials)
        mapped = [mappers.map_accounts_payable(item, period_ref=period_ref) for item in raw]
        result = self.ingest_gateway.ingest_accounts_payable(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_cashflow(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="cashflow", mode=mode)
        period_ref = self._period_ref(credentials)
        mapped = [mappers.map_cashflow(item, period_ref=period_ref) for item in raw]
        result = self.ingest_gateway.ingest_cashflow(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_inventory(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="inventory", mode=mode)
        period_ref = self._period_ref(credentials)
        mapped = [mappers.map_inventory(item, period_ref=period_ref) for item in raw]
        result = self.ingest_gateway.ingest_inventory(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def sync_hr(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="hr", mode=mode)
        period_ref = self._period_ref(credentials)
        mapped = [mappers.map_hr(item, period_ref=period_ref) for item in raw]
        result = self.ingest_gateway.ingest_hr(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        template_result = self._to_template_result(result)
        self._register_template_result(template_result)
        return template_result

    def full_sync(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderSyncResult:
        self.authenticate(company_id=company_id, credentials=credentials)
        return self._run_mode(company_id=company_id, credentials=credentials, mode="full")

    def incremental_sync(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderSyncResult:
        self.authenticate(company_id=company_id, credentials=credentials)
        return self._run_mode(company_id=company_id, credentials=credentials, mode="incremental")

    def disconnect(self, *, company_id: str, credentials: dict[str, Any]) -> None:
        self.authenticate(company_id=company_id, credentials=credentials)

    def _run_mode(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> ProviderSyncResult:
        template_results = (
            self.sync_customers(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_products(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_suppliers(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_sales(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_accounts_receivable(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_accounts_payable(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_cashflow(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_inventory(company_id=company_id, credentials=credentials, mode=mode),
            self.sync_hr(company_id=company_id, credentials=credentials, mode=mode),
        )
        records_read = sum(item.records_read for item in template_results)
        records_imported = sum(item.records_imported for item in template_results)
        records_failed = sum(item.records_failed for item in template_results)
        return ProviderSyncResult(
            provider=self.provider_type,
            records_read=records_read,
            records_imported=records_imported,
            records_failed=records_failed,
            template_results=template_results,
        )

    def _fetch(self, *, credentials: dict[str, Any], endpoint: str, mode: str) -> list[dict[str, Any]]:
        assert self.runtime is not None

        connection_timeout = float(credentials.get("connection_timeout") or self.runtime.config.connection_timeout)
        read_timeout = float(credentials.get("read_timeout") or self.runtime.config.read_timeout)
        write_timeout = float(credentials.get("write_timeout") or self.runtime.config.write_timeout)

        if connection_timeout <= 0 or read_timeout <= 0 or write_timeout <= 0:
            raise ValueError("connection_timeout, read_timeout and write_timeout must be greater than zero")

        use_real_api = bool(credentials.get("use_real_api", False))

        if not use_real_api:
            return resilient_call(
                fn=lambda: self._mock_payload(endpoint=endpoint, mode=mode),
                retry=self.retry_policy,
                rate_limiter=self.rate_limiter,
                circuit_breaker=self.circuit_breaker,
            )

        endpoint_config = self._resolve_endpoint_config(credentials=credentials, endpoint=endpoint)
        if endpoint_config is None:
            raise ValueError(
                f"omie real api endpoint '{endpoint}' not configured. "
                "Configure credentials.omie_endpoints or use use_real_api=false."
            )

        def _call() -> list[dict[str, Any]]:
            return self._fetch_real_endpoint(
                credentials=credentials,
                endpoint=endpoint,
                mode=mode,
                endpoint_config=endpoint_config,
                connection_timeout=connection_timeout,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
            )

        return _call()

    def _fetch_real_endpoint(
        self,
        *,
        credentials: dict[str, Any],
        endpoint: str,
        mode: str,
        endpoint_config: dict[str, Any],
        connection_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> list[dict[str, Any]]:
        assert self.runtime is not None
        runtime = self.runtime

        app_key = str(credentials.get("app_key") or "").strip()
        app_secret = str(credentials.get("app_secret") or "").strip()
        if not app_key or not app_secret:
            raise ValueError("omie credentials require app_key and app_secret")

        base_url = str(credentials.get("omie_base_url") or self._DEFAULT_BASE_URL).strip()
        if not base_url:
            raise ValueError("omie_base_url must be configured when use_real_api=true")
        if not base_url.endswith("/"):
            base_url += "/"

        path = str(endpoint_config.get("path") or "").strip()
        call = str(endpoint_config.get("call") or "").strip()
        if not path or not call:
            raise ValueError(f"invalid omie endpoint configuration for '{endpoint}'")

        url = urljoin(base_url, path)
        page_field = str(endpoint_config.get("page_field") or "pagina")
        page_size_field = str(endpoint_config.get("page_size_field") or "registros_por_pagina")
        requested_page_size = int(endpoint_config.get("page_size") or credentials.get("page_size") or runtime.config.page_size_max)
        page_size_max = int(endpoint_config.get("page_size_max") or runtime.config.page_size_max)
        page_size = min(max(1, requested_page_size), max(1, page_size_max))
        max_pages = int(credentials.get("max_pages") or endpoint_config.get("max_pages") or 500)
        start_page = int(endpoint_config.get("start_page") or 1)
        redundant_retry_seconds = float(credentials.get("redundant_retry_seconds") or 61.0)
        ip_address = str(credentials.get("ip_address") or "default-ip").strip() or "default-ip"
        method_key = runtime.method_key(ip=ip_address, app_key=app_key, method=call)

        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        if max_pages <= 0:
            raise ValueError("max_pages must be greater than zero")
        if redundant_retry_seconds < 0:
            raise ValueError("redundant_retry_seconds must be greater than or equal to zero")

        records: list[dict[str, Any]] = []
        page = start_page
        pages_visited = 0

        while pages_visited < max_pages:
            params = self._build_params(
                credentials=credentials,
                mode=mode,
                endpoint_config=endpoint_config,
                page=page,
                page_field=page_field,
                page_size_field=page_size_field,
                page_size=page_size,
            )

            payload = {
                "call": call,
                "app_key": app_key,
                "app_secret": app_secret,
                "param": [params],
            }
            cache_key = runtime.cache_key(url=url, payload=payload)
            cached = runtime.cache.get(cache_key)
            retries_for_page = 0

            page_started_at = time.monotonic()

            if cached is not None:
                runtime.metrics.inc("cache_hits")
                response_json = cached
            else:
                runtime.metrics.inc("cache_miss")

                def _on_retry(_attempt: int, _exc: Exception, _delay: float) -> None:
                    nonlocal retries_for_page
                    retries_for_page += 1
                    runtime.metrics.inc("retry_total")

                def _request_page() -> dict[str, Any]:
                    blocked_wait = runtime.wait_if_method_blocked(method_key=method_key)
                    if blocked_wait > 0:
                        runtime.metrics.inc("rate_limit_waits")

                    with runtime.worker_pool.slot(method_key):
                        rate_wait = runtime.rate_limiter.acquire(
                            ip=ip_address,
                            app_key=app_key,
                            method=call,
                        )
                        if rate_wait > 0:
                            runtime.metrics.inc("rate_limit_waits")

                        started_at = time.monotonic()
                        runtime.metrics.inc("requests_total")
                        try:
                            response = self._post_json(
                                url=url,
                                payload=payload,
                                connection_timeout=connection_timeout,
                                read_timeout=read_timeout,
                                write_timeout=write_timeout,
                                method_key=method_key,
                                redundant_retry_seconds=redundant_retry_seconds,
                            )
                            runtime.metrics.inc("requests_success")
                            return response
                        except Exception:
                            runtime.metrics.inc("requests_failed")
                            raise
                        finally:
                            runtime.metrics.observe_latency_ms((time.monotonic() - started_at) * 1000)

                # Retry is scoped to the current page so transient failures do not
                # force a full endpoint restart from page 1.
                response_json = resilient_call(
                    fn=_request_page,
                    retry=self.retry_policy,
                    rate_limiter=None,
                    circuit_breaker=self.circuit_breaker,
                    on_retry=_on_retry,
                )
                runtime.cache.set(cache_key, response_json, ttl_seconds=runtime.config.cache_ttl_seconds)

            # Handle Omie SOAP faults
            fault_code = response_json.get("faultcode", "")
            fault_string = response_json.get("faultstring", "")
            if fault_code or fault_string:
                # Error 5113 means no records found - treat as success with empty result
                if "5113" in str(fault_code):
                    break
                # Other faults are real errors
                raise ValueError(f"omie api error {fault_code}: {fault_string}")

            page_records = self._extract_records(response_json, endpoint_config)
            records.extend(page_records)
            runtime.metrics.inc("pages_processed")

            elapsed_ms = (time.monotonic() - page_started_at) * 1000
            total_pages_value = response_json.get("total_de_paginas")
            rate_remaining = runtime.get_rate_limit_remaining(method_key=method_key)
            self._logger.info(
                "omie.page.processed",
                extra={
                    "provider": "omie",
                    "method": call,
                    "page": page,
                    "total_pages": total_pages_value,
                    "duration_ms": int(elapsed_ms),
                    "status_http": 200,
                    "retries": retries_for_page,
                    "rate_limit_remaining": rate_remaining,
                    "records_imported": len(page_records),
                },
            )

            if not self._has_next_page(
                response_json=response_json,
                endpoint_config=endpoint_config,
                current_page=page,
                current_count=len(page_records),
                page_size=page_size,
            ):
                break

            page += 1
            pages_visited += 1

        return records

    def _build_params(
        self,
        *,
        credentials: dict[str, Any],
        mode: str,
        endpoint_config: dict[str, Any],
        page: int,
        page_field: str,
        page_size_field: str,
        page_size: int,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            page_field: page,
            page_size_field: page_size,
            **self._safe_dict(endpoint_config.get("params")),
            **self._safe_dict(credentials.get("common_params")),
            **self._safe_dict(credentials.get(f"{mode}_params")),
            **self._safe_dict(credentials.get(f"{mode}_{endpoint_config.get('call', '')}_params")),
        }

        if mode == "incremental":
            params.update(self._incremental_period_params(credentials, endpoint_config))

        return params

    def _post_json(
        self,
        *,
        url: str,
        payload: dict[str, Any],
        connection_timeout: float,
        read_timeout: float,
        write_timeout: float,
        method_key: str,
        redundant_retry_seconds: float,
    ) -> dict[str, Any]:
        assert self.runtime is not None
        runtime = self.runtime

        effective_timeout = max(connection_timeout, read_timeout, write_timeout)
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=effective_timeout) as response:
                rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
                if rate_limit_remaining:
                    runtime.set_rate_limit_remaining(method_key=method_key, remaining=rate_limit_remaining)
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = ""

            if exc.code == 425:
                wait_seconds = max(
                    runtime.config.http_425_cooldown_seconds,
                    self._extract_retry_after_header(exc),
                    self._extract_retry_seconds(body),
                )
                runtime.block_method(method_key=method_key, seconds=wait_seconds)
                raise RetryableProviderError(
                    "omie method temporarily blocked (425); retry after cooldown",
                    retry_after_seconds=wait_seconds,
                ) from exc

            if exc.code == 429:
                wait_seconds = max(1.0, self._extract_retry_after_header(exc), self._extract_retry_seconds(body))
                raise RetryableProviderError(
                    "omie rate limit reached (429); retrying with backoff",
                    retry_after_seconds=wait_seconds,
                ) from exc

            if exc.code in {500, 503} and self._is_redundant_fault(body):
                retry_after = max(redundant_retry_seconds, self._extract_retry_seconds(body))
                raise RetryableProviderError(
                    "omie redundant request detected; retrying after cooldown window",
                    retry_after_seconds=retry_after,
                ) from exc

            if exc.code in {500, 503}:
                retry_after = max(1.0, self._extract_retry_after_header(exc), self._extract_retry_seconds(body))
                raise RetryableProviderError(
                    f"omie transient server error ({exc.code}); retrying",
                    retry_after_seconds=retry_after,
                ) from exc

            raise ValueError(f"omie request failed with status {exc.code}: {body[:300]}") from exc
        except URLError as exc:
            raise RetryableProviderError(
                f"omie transient network error: {exc.reason}",
                retry_after_seconds=1.0,
            ) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("omie response is not valid json") from exc

        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {"items": data}
        raise ValueError("omie response has unsupported shape")

    @staticmethod
    def _is_redundant_fault(body: str) -> bool:
        text = body.lower()
        return "consumo redundante" in text or "(redundant)" in text or "redundant" in text

    @staticmethod
    def _extract_retry_seconds(body: str) -> float:
        match = re.search(r"aguarde\s+(\d+)\s+segundos", body, flags=re.IGNORECASE)
        if match is not None:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0

        match = re.search(r"wait\s+(\d+)\s+seconds", body, flags=re.IGNORECASE)
        if match is not None:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def _extract_retry_after_header(exc: HTTPError) -> float:
        headers = getattr(exc, "headers", None)
        if headers is None:
            return 0.0
        raw = headers.get("Retry-After")
        if raw is None:
            return 0.0
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0

    def _extract_records(self, response_json: dict[str, Any], endpoint_config: dict[str, Any]) -> list[dict[str, Any]]:
        list_path = endpoint_config.get("list_path")
        if isinstance(list_path, str) and list_path.strip():
            selected = self._select_path(response_json, list_path)
            if isinstance(selected, list):
                return [item for item in selected if isinstance(item, dict)]

        for value in response_json.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        items = response_json.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]

        return []

    def _has_next_page(
        self,
        *,
        response_json: dict[str, Any],
        endpoint_config: dict[str, Any],
        current_page: int,
        current_count: int,
        page_size: int,
    ) -> bool:
        total_pages_key = str(endpoint_config.get("total_pages_key") or "total_de_paginas")
        current_page_key = str(endpoint_config.get("current_page_key") or "pagina")

        total_pages_raw = response_json.get(total_pages_key)
        if total_pages_raw is not None:
            try:
                total_pages = int(total_pages_raw)
                page_value = int(response_json.get(current_page_key, current_page))
                return page_value < total_pages
            except (TypeError, ValueError):
                pass

        if current_count == 0:
            return False

        return current_count >= page_size

    def _resolve_endpoint_config(self, *, credentials: dict[str, Any], endpoint: str) -> dict[str, Any] | None:
        configured = self._safe_dict(credentials.get("omie_endpoints")).get(endpoint)
        if isinstance(configured, dict):
            base = self._DEFAULT_ENDPOINTS.get(endpoint, {}).copy()
            base.update(configured)
            return base
        if endpoint in self._DEFAULT_ENDPOINTS:
            return self._DEFAULT_ENDPOINTS[endpoint].copy()
        return None

    @staticmethod
    def _safe_dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _select_path(data: dict[str, Any], path: str) -> Any:
        current: Any = data
        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
                continue
            return None
        return current

    @staticmethod
    def _incremental_period_params(credentials: dict[str, Any], endpoint_config: dict[str, Any]) -> dict[str, Any]:
        last_success_sync = str(credentials.get("last_success_sync") or "").strip()
        if last_success_sync:
            start_field = str(endpoint_config.get("incremental_start_field") or "data_de")
            end_field = str(endpoint_config.get("incremental_end_field") or "data_ate")
            date_format = str(endpoint_config.get("incremental_date_format") or "%d/%m/%Y")
            try:
                parsed = datetime.fromisoformat(last_success_sync.replace("Z", "+00:00"))
                now_utc = datetime.now(timezone.utc)
                return {
                    start_field: parsed.strftime(date_format),
                    end_field: now_utc.strftime(date_format),
                }
            except ValueError:
                pass

        period_ref = str(credentials.get("period_ref") or "").strip()
        if len(period_ref) != 7 or "-" not in period_ref:
            return {}
        year_str, month_str = period_ref.split("-", 1)
        try:
            year = int(year_str)
            month = int(month_str)
            if month < 1 or month > 12:
                return {}
        except ValueError:
            return {}

        start_day = datetime(year, month, 1)
        end_day = datetime(year, month, monthrange(year, month)[1])
        start_field = str(endpoint_config.get("incremental_start_field") or "data_de")
        end_field = str(endpoint_config.get("incremental_end_field") or "data_ate")
        date_format = str(endpoint_config.get("incremental_date_format") or "%d/%m/%Y")
        return {
            start_field: start_day.strftime(date_format),
            end_field: end_day.strftime(date_format),
        }

    @staticmethod
    def _period_ref(credentials: dict[str, Any]) -> str:
        return str(credentials.get("period_ref") or datetime.utcnow().strftime("%Y-%m"))

    @staticmethod
    def _correlation_id(credentials: dict[str, Any]) -> str | None:
        raw = credentials.get("correlation_id")
        return str(raw) if raw is not None else None

    @staticmethod
    def _to_template_result(result) -> TemplateSyncResult:
        return TemplateSyncResult(
            template=result.template,
            records_read=result.records_read,
            records_imported=result.records_imported,
            records_failed=result.records_failed,
            import_job_id=result.import_job_id,
            ingest_event_id=result.ingest_event_id,
            pipeline_run_id=result.pipeline_run_id,
        )

    def _register_template_result(self, result: TemplateSyncResult) -> None:
        assert self.runtime is not None
        runtime = self.runtime
        runtime.metrics.inc("records_imported", float(result.records_imported))
        runtime.metrics.inc("records_failed", float(result.records_failed))

    @staticmethod
    def _mock_payload(*, endpoint: str, mode: str) -> list[dict[str, Any]]:
        if mode == "incremental" and endpoint not in {"sales", "cashflow", "accounts_receivable", "accounts_payable"}:
            return []

        samples: dict[str, list[dict[str, Any]]] = {
            "customers": [
                {
                    "codigo_cliente_omie": "CLI-OMIE-1",
                    "razao_social": "Acme LTDA",
                    "nome_fantasia": "Acme",
                    "cnpj_cpf": "12345678901234",
                    "email": "financeiro@acme.com",
                    "telefone1_ddd": "+5511999999999",
                }
            ],
            "products": [
                {
                    "codigo_produto": "PRD-OMIE-1",
                    "codigo": "SKU-1",
                    "descricao": "Produto Omie",
                    "unidade": "UN",
                    "valor_unitario": 120.0,
                    "valor_custo": 80.0,
                }
            ],
            "sales": [
                {
                    "codigo_pedido": "PED-1",
                    "numero_pedido": "NF-1",
                    "data_emissao": "2026-07-10",
                    "codigo_produto": "PRD-OMIE-1",
                    "codigo_cliente": "CLI-OMIE-1",
                    "valor_total_pedido": 1200.0,
                    "valor_impostos": 120.0,
                    "valor_desconto": 20.0,
                    "valor_devolucao": 0.0,
                    "valor_liquido": 1060.0,
                    "quantidade": 10,
                    "custo_total": 800.0,
                }
            ],
            "accounts_receivable": [
                {
                    "codigo_lancamento": "AR-1",
                    "codigo_cliente": "CLI-OMIE-1",
                    "numero_documento": "DUP-1",
                    "data_emissao": "2026-07-10",
                    "data_vencimento": "2026-07-30",
                    "valor_documento": 1060.0,
                    "valor_recebido": 0.0,
                    "valor_aberto": 1060.0,
                    "dias_atraso": 0,
                    "status": "open",
                }
            ],
            "accounts_payable": [
                {
                    "codigo_lancamento": "AP-1",
                    "codigo_fornecedor": "FOR-1",
                    "numero_documento": "BILL-1",
                    "data_emissao": "2026-07-08",
                    "data_vencimento": "2026-07-28",
                    "valor_documento": 800.0,
                    "valor_pago": 0.0,
                    "valor_aberto": 800.0,
                    "dias_atraso": 0,
                    "status": "open",
                }
            ],
            "cashflow": [
                {
                    "codigo_lancamento": "CF-1",
                    "data_lancamento": "2026-07-10",
                    "tipo_fluxo": "operational",
                    "conta": "main",
                    "valor_entrada": 1200.0,
                    "valor_saida": 800.0,
                    "descricao": "fluxo caixa omie",
                }
            ],
            "inventory": [
                {
                    "codigo_item": "INV-1",
                    "codigo_produto": "PRD-OMIE-1",
                    "codigo_almoxarifado": "WH-1",
                    "data_snapshot": "2026-07-10",
                    "estoque_inicial": 100,
                    "estoque_final": 90,
                    "custo_medio": 80,
                    "giro": 2.0,
                    "dias_estoque": 18.0,
                }
            ],
            "hr": [
                {
                    "codigo_lote": "HR-1",
                    "colaboradores_total": 40,
                    "colaboradores_ativos": 38,
                    "colaboradores_desligados": 2,
                    "folha_total": 120000.0,
                    "horas_trabalhadas": 6800.0,
                }
            ],
        }
        return samples.get(endpoint, [])
