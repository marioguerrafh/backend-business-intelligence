"""Job dispatcher for executing synchronization jobs."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from app.modules.integrations.application.provider_registry import ProviderRegistry
from app.modules.integrations.infrastructure.security import CredentialCipher
from app.modules.synchronization.domain.entities import SyncJob
from app.modules.synchronization.domain.value_objects import JobStatus, SyncDomain
from app.modules.synchronization.infrastructure.repositories import CheckpointRepository, JobRepository
from app.modules.synchronization.infrastructure.sync_runtime import SyncRuntime


@dataclass(slots=True)
class JobDispatcher:
    """Dispatches synchronization jobs to providers."""

    job_repository: JobRepository
    checkpoint_repository: CheckpointRepository
    provider_registry: ProviderRegistry
    credential_cipher: CredentialCipher
    runtime: SyncRuntime
    _logger: logging.Logger = logging.getLogger("app.synchronization.dispatcher")

    def execute_job(self, job: SyncJob, encrypted_credentials: bytes) -> None:
        """Execute a synchronization job."""
        try:
            # Mark job as running
            job.start()
            self.job_repository.update_job_status(
                job.job_id,
                JobStatus.RUNNING,
                started_at=job.started_at,
            )
            self.runtime.register_job_started(job.job_id)

            # Get provider
            provider = self.provider_registry.get(job.provider)
            credentials = self.credential_cipher.decrypt(encrypted_credentials)

            # Inject window dates if present
            if job.window:
                credentials = dict(credentials)
                credentials["period_start"] = job.window.start_date.isoformat()
                credentials["period_end"] = job.window.end_date.isoformat()
                credentials["period_ref"] = job.window.start_date.strftime("%Y-%m")

            # Inject checkpoint if present
            if job.checkpoint_id:
                checkpoint = self.checkpoint_repository.get_checkpoint(job.checkpoint_id)
                if checkpoint and checkpoint.last_page:
                    credentials["start_page"] = checkpoint.last_page + 1
                    self.runtime.register_checkpoint_restored(job.domain.value)

            # Map domain to provider method
            sync_method = self._get_sync_method_for_domain(job.domain)

            # Execute provider sync
            result = getattr(provider, sync_method)(
                company_id=job.company_id,
                credentials=credentials,
                mode=job.mode,
            )

            # Mark job as completed
            job.complete(
                records_read=result.records_read,
                records_imported=result.records_imported,
                records_failed=result.records_failed,
                pages_processed=1,  # Provider doesn't expose this yet
            )

            self.job_repository.update_job_status(
                job.job_id,
                JobStatus.COMPLETED,
                completed_at=job.completed_at,
                records_read=job.records_read,
                records_imported=job.records_imported,
                records_failed=job.records_failed,
                pages_processed=job.pages_processed,
            )

            self.runtime.register_job_completed(
                job.job_id,
                domain=job.domain.value,
                records_imported=job.records_imported,
                pages=job.pages_processed,
            )

            # Mark checkpoint as completed if present
            if job.checkpoint_id:
                self.checkpoint_repository.mark_checkpoint_completed(job.checkpoint_id)

            # Register window processed
            if job.window:
                self.runtime.register_window_processed(job.domain.value)

            self._logger.info(
                f"Job {job.job_id} completed successfully",
                extra={
                    "job_id": job.job_id,
                    "company_id": job.company_id,
                    "provider": job.provider,
                    "domain": job.domain.value,
                    "records_imported": job.records_imported,
                    "duration_seconds": job.duration_seconds,
                },
            )

        except Exception as exc:
            # Mark job as failed
            error_message = str(exc)
            job.fail(error_message)

            self.job_repository.update_job_status(
                job.job_id,
                JobStatus.FAILED,
                failed_at=job.failed_at,
                error_message=error_message,
                retry_count=job.retry_count,
            )

            self.runtime.register_job_failed(job.job_id, domain=job.domain.value)

            # Mark checkpoint as failed if present
            if job.checkpoint_id:
                self.checkpoint_repository.mark_checkpoint_failed(job.checkpoint_id)

            self._logger.error(
                f"Job {job.job_id} failed: {error_message}",
                extra={
                    "job_id": job.job_id,
                    "company_id": job.company_id,
                    "provider": job.provider,
                    "domain": job.domain.value,
                    "error": error_message,
                },
                exc_info=True,
            )

            # Re-raise for potential retry logic
            raise

    @staticmethod
    def _get_sync_method_for_domain(domain: SyncDomain) -> str:
        """Map domain to provider sync method name."""
        mapping = {
            SyncDomain.CUSTOMERS: "sync_customers",
            SyncDomain.PRODUCTS: "sync_products",
            SyncDomain.SALES: "sync_sales",
            SyncDomain.ACCOUNTS_RECEIVABLE: "sync_accounts_receivable",
            SyncDomain.ACCOUNTS_PAYABLE: "sync_accounts_payable",
            SyncDomain.CASHFLOW: "sync_cashflow",
            SyncDomain.INVENTORY: "sync_inventory",
            SyncDomain.HR: "sync_hr",
            SyncDomain.SUPPLIERS: "sync_suppliers",
        }
        return mapping[domain]
