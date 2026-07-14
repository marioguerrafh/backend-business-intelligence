from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.business.infrastructure.container import build_customer_container
from app.modules.business.infrastructure.product_container import build_product_container
from app.modules.imports.infrastructure.repositories import ImportRepository
from app.modules.integrations.application.provider_registry import ProviderRegistry
from app.modules.integrations.application.service import IntegrationService
from app.modules.integrations.infrastructure.ingest_gateway import IntegrationIngestGateway
from app.modules.integrations.infrastructure.repositories import IntegrationRepository
from app.modules.integrations.infrastructure.security import CredentialCipher
from app.modules.integrations.providers.omie.config import load_omie_provider_config
from app.modules.integrations.providers.bling.provider import BlingProvider
from app.modules.integrations.providers.conta_azul.provider import ContaAzulProvider
from app.modules.integrations.providers.dynamics.provider import DynamicsProvider
from app.modules.integrations.providers.omie.provider import OmieProvider
from app.modules.integrations.providers.omie.runtime import OmieRuntime
from app.modules.integrations.providers.oracle.provider import OracleProvider
from app.modules.integrations.providers.sankhya.provider import SankhyaProvider
from app.modules.integrations.providers.sap.provider import SAPProvider
from app.modules.integrations.providers.senior.provider import SeniorProvider
from app.modules.integrations.providers.tiny.provider import TinyProvider
from app.modules.integrations.providers.totvs.provider import TOTVSProvider
from app.modules.integrations.providers.shared.resilience import CircuitBreaker, RateLimiter, RetryPolicy
from app.modules.pipeline.infrastructure.container import build_pipeline_container


@dataclass(slots=True)
class IntegrationsContainer:
    service: IntegrationService


_OMIE_RUNTIME: OmieRuntime | None = None


def _get_omie_runtime() -> OmieRuntime:
    global _OMIE_RUNTIME
    if _OMIE_RUNTIME is None:
        _OMIE_RUNTIME = OmieRuntime(load_omie_provider_config())
    return _OMIE_RUNTIME


def build_integrations_container(session: Session) -> IntegrationsContainer:
    repository = IntegrationRepository(session=session)
    import_repository = ImportRepository(session=session)
    customer_container = build_customer_container(session)
    product_container = build_product_container(session)
    pipeline_container = build_pipeline_container(session)

    ingest_gateway = IntegrationIngestGateway(
        import_repository=import_repository,
        upsert_customer=customer_container.upsert_customer,
        upsert_product=product_container.upsert_product,
        pipeline_coordinator=pipeline_container.coordinator,
    )

    omie_config = load_omie_provider_config()

    omie_provider = OmieProvider(
        ingest_gateway=ingest_gateway,
        retry_policy=RetryPolicy(
            max_attempts=max(1, omie_config.retry_attempts),
            base_delay_seconds=max(0.0, omie_config.backoff_base_seconds),
            backoff_strategy="exponential",
            max_delay_seconds=max(0.0, omie_config.backoff_max_seconds),
        ),
        # Generic limiter remains available for non-real API paths.
        rate_limiter=RateLimiter(max_requests_per_second=max(1, omie_config.max_parallel_requests)),
        circuit_breaker=CircuitBreaker(
            failure_threshold=max(1, omie_config.circuit_breaker_threshold),
            recovery_timeout_seconds=max(1.0, omie_config.circuit_breaker_timeout),
        ),
        runtime=_get_omie_runtime(),
    )

    registry = ProviderRegistry(
        providers={
            "omie": omie_provider,
            "conta_azul": ContaAzulProvider(),
            "tiny": TinyProvider(),
            "bling": BlingProvider(),
            "sap": SAPProvider(),
            "totvs": TOTVSProvider(),
            "senior": SeniorProvider(),
            "sankhya": SankhyaProvider(),
            "oracle": OracleProvider(),
            "dynamics": DynamicsProvider(),
        }
    )

    service = IntegrationService(
        repository=repository,
        provider_registry=registry,
        credential_cipher=CredentialCipher.from_settings(),
    )
    return IntegrationsContainer(service=service)
