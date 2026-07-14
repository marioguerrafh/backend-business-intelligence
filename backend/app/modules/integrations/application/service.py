from __future__ import annotations

import time
from dataclasses import dataclass

from app.modules.integrations.application.contracts import (
    ConnectIntegrationCommand,
    IntegrationConnectionResult,
    IntegrationSyncJobResult,
    RunIntegrationSyncCommand,
)
from app.modules.integrations.application.provider_registry import ProviderRegistry
from app.modules.integrations.infrastructure.repositories import IntegrationRepository
from app.modules.integrations.infrastructure.security import CredentialCipher


@dataclass(slots=True)
class IntegrationService:
    repository: IntegrationRepository
    provider_registry: ProviderRegistry
    credential_cipher: CredentialCipher

    def connect(self, command: ConnectIntegrationCommand) -> IntegrationConnectionResult:
        provider = self.provider_registry.get(command.provider)
        provider.authenticate(company_id=command.company_id, credentials=command.credentials)

        encrypted = self.credential_cipher.encrypt(command.credentials)
        model = self.repository.create_connection(
            company_id=command.company_id,
            provider=command.provider,
            encrypted_credentials=encrypted,
        )
        return self._to_connection_result(model)

    def list_integrations(self, *, company_id: str) -> list[IntegrationConnectionResult]:
        return [self._to_connection_result(item) for item in self.repository.list_connections(company_id=company_id)]

    def get_integration(self, *, company_id: str, integration_id: str) -> IntegrationConnectionResult:
        model = self.repository.get_connection(company_id=company_id, connection_id=integration_id)
        if model is None:
            raise ValueError("integration connection not found")
        return self._to_connection_result(model)

    def disconnect(self, *, company_id: str, integration_id: str) -> None:
        model = self.repository.get_connection(company_id=company_id, connection_id=integration_id)
        if model is None:
            raise ValueError("integration connection not found")

        provider = self.provider_registry.get(model.provider)
        credentials = self.credential_cipher.decrypt(model.credentials)
        provider.disconnect(company_id=company_id, credentials=credentials)
        self.repository.mark_disconnected(company_id=company_id, connection_id=integration_id)

    def sync(self, command: RunIntegrationSyncCommand) -> IntegrationSyncJobResult:
        connection = self.repository.get_connection(company_id=command.company_id, connection_id=command.integration_id)
        if connection is None:
            raise ValueError("integration connection not found")
        if not connection.enabled:
            raise ValueError("integration connection is disabled")

        provider = self.provider_registry.get(connection.provider)
        credentials = self.credential_cipher.decrypt(connection.credentials)

        job = self.repository.create_sync_job(provider=connection.provider, company_id=command.company_id)
        started = time.monotonic()

        self.repository.publish_event(
            provider=connection.provider,
            company_id=command.company_id,
            topic="integration.sync.started.v1",
            payload={
                "job_id": job.job_id,
                "provider": connection.provider,
                "company_id": command.company_id,
                "mode": command.mode,
            },
        )

        try:
            if command.mode == "full":
                result = provider.full_sync(company_id=command.company_id, credentials=credentials)
            else:
                result = provider.incremental_sync(company_id=command.company_id, credentials=credentials)

            pipeline_run_id = next((item.pipeline_run_id for item in result.template_results if item.pipeline_run_id), None)
            completed = self.repository.complete_sync_job(
                job_id=job.job_id,
                status="success",
                records_read=result.records_read,
                records_imported=result.records_imported,
                records_failed=result.records_failed,
                pipeline_run_id=pipeline_run_id,
            )
            self.repository.mark_sync_success(company_id=command.company_id, connection_id=command.integration_id)

            self.repository.publish_event(
                provider=connection.provider,
                company_id=command.company_id,
                topic="integration.sync.completed.v1",
                payload={
                    "job_id": job.job_id,
                    "provider": connection.provider,
                    "company_id": command.company_id,
                    "records_read": result.records_read,
                    "records_imported": result.records_imported,
                    "records_failed": result.records_failed,
                    "pipeline_run_id": pipeline_run_id,
                },
            )
            self.repository.add_log(
                company_id=command.company_id,
                provider=connection.provider,
                endpoint=f"sync:{command.mode}",
                request_payload={
                    "job_id": job.job_id,
                    "mode": command.mode,
                    "provider": connection.provider,
                    "credentials": self.credential_cipher.mask(credentials),
                },
                duration_ms=int((time.monotonic() - started) * 1000),
                status="success",
                error_message=None,
            )
            return self._to_job_result(completed)
        except Exception as exc:
            completed = self.repository.complete_sync_job(
                job_id=job.job_id,
                status="failed",
                records_read=0,
                records_imported=0,
                records_failed=0,
                pipeline_run_id=None,
            )
            self.repository.mark_sync_failed(company_id=command.company_id, connection_id=command.integration_id)
            self.repository.publish_event(
                provider=connection.provider,
                company_id=command.company_id,
                topic="integration.sync.failed.v1",
                payload={
                    "job_id": job.job_id,
                    "provider": connection.provider,
                    "company_id": command.company_id,
                    "error": str(exc),
                },
            )
            self.repository.add_log(
                company_id=command.company_id,
                provider=connection.provider,
                endpoint=f"sync:{command.mode}",
                request_payload={
                    "job_id": job.job_id,
                    "mode": command.mode,
                    "provider": connection.provider,
                    "credentials": self.credential_cipher.mask(credentials),
                },
                duration_ms=int((time.monotonic() - started) * 1000),
                status="failed",
                error_message=str(exc),
            )
            raise ValueError(str(exc)) from exc

    def list_jobs(self, *, company_id: str) -> list[IntegrationSyncJobResult]:
        return [self._to_job_result(item) for item in self.repository.list_jobs(company_id=company_id)]

    def get_job(self, *, company_id: str, job_id: str) -> IntegrationSyncJobResult:
        model = self.repository.get_job(company_id=company_id, job_id=job_id)
        if model is None:
            raise ValueError("integration sync job not found")
        return self._to_job_result(model)

    @staticmethod
    def _to_connection_result(model) -> IntegrationConnectionResult:
        return IntegrationConnectionResult(
            id=model.id,
            company_id=model.company_id,
            provider=model.provider,
            status=model.status,
            enabled=bool(model.enabled),
            last_sync=model.last_sync,
            last_success_sync=model.last_success_sync,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_job_result(model) -> IntegrationSyncJobResult:
        return IntegrationSyncJobResult(
            job_id=model.job_id,
            provider=model.provider,
            company_id=model.company_id,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at,
            duration_ms=model.duration_ms,
            records_read=model.records_read,
            records_imported=model.records_imported,
            records_failed=model.records_failed,
            pipeline_run_id=model.pipeline_run_id,
        )
