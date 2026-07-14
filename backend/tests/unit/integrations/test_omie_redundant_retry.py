import io
from typing import Any
from urllib.error import HTTPError

import pytest

from app.modules.integrations.providers.omie.provider import OmieProvider
from app.modules.integrations.providers.shared.resilience import (
    CircuitBreaker,
    RateLimiter,
    RetryPolicy,
    RetryableProviderError,
    resilient_call,
)


def _provider() -> OmieProvider:
    return OmieProvider(
        ingest_gateway=None,  # type: ignore[arg-type]
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0.1),
        rate_limiter=RateLimiter(max_requests_per_second=100),
        circuit_breaker=CircuitBreaker(failure_threshold=5, recovery_timeout_seconds=20.0),
    )


def test_post_json_redundant_fault_raises_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    body = (
        '{"faultstring":"ERROR: Consumo redundante detectado. '
        'Aguarde 60 segundos para tentar novamente (REDUNDANT).",'
        '"faultcode":"SOAP-ENV:Client-6"}'
    )

    def fake_urlopen(*args: Any, **kwargs: Any):
        raise HTTPError(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=io.BytesIO(body.encode("utf-8")),
        )

    monkeypatch.setattr("app.modules.integrations.providers.omie.provider.urlopen", fake_urlopen)

    provider = _provider()
    with pytest.raises(RetryableProviderError) as exc_info:
        provider._post_json(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            payload={"call": "ListarClientes", "param": [{}]},
            connection_timeout=1.0,
            read_timeout=1.0,
            write_timeout=1.0,
            method_key="default-ip|key|ListarClientes",
            redundant_retry_seconds=61.0,
        )

    assert exc_info.value.retry_after_seconds is not None
    assert exc_info.value.retry_after_seconds >= 60.0


def test_resilient_call_honors_retry_after_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("app.modules.integrations.providers.shared.resilience.time.sleep", fake_sleep)

    attempts = {"count": 0}

    def flaky_call() -> int:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RetryableProviderError("temporary cooldown", retry_after_seconds=2.5)
        return 123

    result = resilient_call(
        fn=flaky_call,
        retry=RetryPolicy(max_attempts=2, base_delay_seconds=0.1),
        rate_limiter=RateLimiter(max_requests_per_second=100),
        circuit_breaker=CircuitBreaker(failure_threshold=5, recovery_timeout_seconds=20.0),
    )

    assert result == 123
    assert attempts["count"] == 2
    assert slept
    assert slept[0] >= 2.5


def test_fetch_real_endpoint_retries_only_failed_page(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = _provider()
    calls: list[int] = []

    def fake_post_json(
        self: OmieProvider,
        *,
        url: str,
        payload: dict[str, Any],
        connection_timeout: float,
        read_timeout: float,
        write_timeout: float,
        method_key: str,
        redundant_retry_seconds: float,
    ) -> dict[str, Any]:
        page = int(payload["param"][0]["pagina"])
        calls.append(page)

        if page == 2 and calls.count(2) == 1:
            raise RetryableProviderError("temporary cooldown", retry_after_seconds=0.0)

        return {
            "pagina": page,
            "total_de_paginas": 2,
            "clientes_cadastro": [{"codigo_cliente_omie": f"CLI-{page}"}],
        }

    monkeypatch.setattr(OmieProvider, "_post_json", fake_post_json)

    records = provider._fetch_real_endpoint(
        credentials={"app_key": "key", "app_secret": "secret"},
        endpoint="customers",
        mode="full",
        endpoint_config=dict(provider._DEFAULT_ENDPOINTS["customers"]),
        connection_timeout=1.0,
        read_timeout=1.0,
        write_timeout=1.0,
    )

    assert len(records) == 2
    # Must retry page 2 without restarting from page 1.
    assert calls == [1, 2, 2]


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_post_json_client_errors_are_not_retryable(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    body = '{"faultstring":"client error"}'

    def fake_urlopen(*args: Any, **kwargs: Any):
        raise HTTPError(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            code=status,
            msg="Client Error",
            hdrs=None,
            fp=io.BytesIO(body.encode("utf-8")),
        )

    monkeypatch.setattr("app.modules.integrations.providers.omie.provider.urlopen", fake_urlopen)

    provider = _provider()
    with pytest.raises(ValueError):
        provider._post_json(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            payload={"call": "ListarClientes", "param": [{}]},
            connection_timeout=1.0,
            read_timeout=1.0,
            write_timeout=1.0,
            method_key="default-ip|key|ListarClientes",
            redundant_retry_seconds=61.0,
        )


@pytest.mark.parametrize("status", [429, 500, 503])
def test_post_json_transient_errors_are_retryable(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    body = '{"faultstring":"transient"}'

    def fake_urlopen(*args: Any, **kwargs: Any):
        raise HTTPError(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            code=status,
            msg="Transient Error",
            hdrs={"Retry-After": "1"},
            fp=io.BytesIO(body.encode("utf-8")),
        )

    monkeypatch.setattr("app.modules.integrations.providers.omie.provider.urlopen", fake_urlopen)

    provider = _provider()
    with pytest.raises(RetryableProviderError):
        provider._post_json(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            payload={"call": "ListarClientes", "param": [{}]},
            connection_timeout=1.0,
            read_timeout=1.0,
            write_timeout=1.0,
            method_key="default-ip|key|ListarClientes",
            redundant_retry_seconds=61.0,
        )


def test_post_json_http_425_blocks_method(monkeypatch: pytest.MonkeyPatch) -> None:
    body = '{"faultstring":"Too Early"}'

    def fake_urlopen(*args: Any, **kwargs: Any):
        raise HTTPError(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            code=425,
            msg="Too Early",
            hdrs={"Retry-After": "2"},
            fp=io.BytesIO(body.encode("utf-8")),
        )

    monkeypatch.setattr("app.modules.integrations.providers.omie.provider.urlopen", fake_urlopen)

    provider = _provider()
    method_key = "default-ip|key|ListarClientes"
    with pytest.raises(RetryableProviderError):
        provider._post_json(
            url="https://app.omie.com.br/api/v1/geral/clientes/",
            payload={"call": "ListarClientes", "param": [{}]},
            connection_timeout=1.0,
            read_timeout=1.0,
            write_timeout=1.0,
            method_key=method_key,
            redundant_retry_seconds=61.0,
        )

    assert provider.runtime is not None
    waited = provider.runtime.wait_if_method_blocked(method_key=method_key)
    assert waited >= 0.0
