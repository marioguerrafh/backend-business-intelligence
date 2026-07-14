from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.integrations.application.provider_interface import (
    ProviderAuthResult,
    ProviderSyncResult,
    TemplateSyncResult,
)
from app.modules.integrations.infrastructure.ingest_gateway import IntegrationIngestGateway
from app.modules.integrations.providers.omie import mappers
from app.modules.integrations.providers.shared.resilience import CircuitBreaker, RateLimiter, RetryPolicy, resilient_call


@dataclass(slots=True)
class OmieProvider:
    ingest_gateway: IntegrationIngestGateway
    retry_policy: RetryPolicy
    rate_limiter: RateLimiter
    circuit_breaker: CircuitBreaker
    provider_type: str = "omie"

    def authenticate(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderAuthResult:
        app_key = str(credentials.get("app_key") or "").strip()
        app_secret = str(credentials.get("app_secret") or "").strip()
        if not app_key or not app_secret:
            raise ValueError("omie credentials require app_key and app_secret")
        return ProviderAuthResult(connected=True, external_account_id=f"omie:{company_id}:{app_key[:4]}")

    def health(self, *, company_id: str, credentials: dict[str, Any]) -> dict[str, Any]:
        self.authenticate(company_id=company_id, credentials=credentials)
        return {"provider": "omie", "status": "ok"}

    def sync_customers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="customers", mode=mode)
        mapped = [mappers.map_customer(item) for item in raw]
        result = self.ingest_gateway.ingest_customers(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        return self._to_template_result(result)

    def sync_products(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        raw = self._fetch(credentials=credentials, endpoint="products", mode=mode)
        mapped = [mappers.map_product(item) for item in raw]
        result = self.ingest_gateway.ingest_products(
            company_id=company_id,
            source_system="omie",
            records=mapped,
            correlation_id=self._correlation_id(credentials),
        )
        return self._to_template_result(result)

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
        return self._to_template_result(result)

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
        return self._to_template_result(result)

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
        return self._to_template_result(result)

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
        return self._to_template_result(result)

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
        return self._to_template_result(result)

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
        return self._to_template_result(result)

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
        timeout_seconds = float(credentials.get("timeout_seconds") or 5.0)

        def _call() -> list[dict[str, Any]]:
            data = self._mock_payload(endpoint=endpoint, mode=mode)
            if timeout_seconds <= 0:
                raise ValueError("timeout must be greater than zero")
            return data

        return resilient_call(
            fn=_call,
            retry=self.retry_policy,
            rate_limiter=self.rate_limiter,
            circuit_breaker=self.circuit_breaker,
        )

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
