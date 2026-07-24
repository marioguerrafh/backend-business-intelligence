"""Synchronization orchestrator - coordinates all sync operations."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.modules.synchronization.application.job_dispatcher import JobDispatcher
from app.modules.synchronization.domain.entities import SyncBatch, SyncJob, TimeWindow
from app.modules.synchronization.domain.value_objects import JobPriority, JobStatus, SyncDomain
from app.modules.synchronization.infrastructure.repositories import CheckpointRepository, JobRepository
from app.modules.synchronization.infrastructure.sync_runtime import SyncRuntime
from app.modules.synchronization.infrastructure.window_manager import WindowManager
from app.modules.synchronization.infrastructure.worker_pool import WorkerPool


@dataclass(slots=True)
class SynchronizationOrchestrator:
    """Orchestrates synchronization operations across all providers."""

    job_repository: JobRepository
    checkpoint_repository: CheckpointRepository
    job_dispatcher: JobDispatcher
    window_manager: WindowManager
    worker_pool: WorkerPool
    runtime: SyncRuntime
    _logger: logging.Logger = logging.getLogger("app.synchronization.orchestrator")

    def start(self) -> None:
        """Start the orchestrator."""
        self.worker_pool.start()
        self._logger.info("Synchronization orchestrator started")

    def shutdown(self) -> None:
        """Shutdown the orchestrator."""
        self.worker_pool.shutdown(wait=True)
        self._logger.info("Synchronization orchestrator shut down")

    def schedule_full_sync(
        self,
        *,
        company_id: str,
        provider: str,
        domains: list[SyncDomain],
        encrypted_credentials: bytes,
        window_config: dict[str, int],  # domain -> window_days
        priority_config: dict[str, JobPriority] | None = None,
    ) -> SyncBatch:
        """Schedule a full sync with multiple domains as separate jobs."""
        batch = SyncBatch.create(company_id=company_id, provider=provider)

        for domain in domains:
            window_days = window_config.get(domain.value, 30)
            priority = (priority_config or {}).get(domain.value, JobPriority.NORMAL)

            # Create checkpoint for this domain
            checkpoint = self.checkpoint_repository.create_checkpoint(
                company_id=company_id,
                provider=provider,
                domain=domain,
            )
            self.runtime.register_checkpoint_created(domain.value)

            # Calculate windows for this domain
            windows = self.window_manager.calculate_windows_for_domain(
                domain=domain.value,
                window_days=window_days,
            )

            # Create a job for each window
            for window in windows:
                job = SyncJob.create(
                    company_id=company_id,
                    provider=provider,
                    domain=domain,
                    priority=priority,
                    window=window,
                    mode="full",
                    checkpoint_id=checkpoint.checkpoint_id,
                )

                self.job_repository.create_job(job)
                batch.add_job(job)

                # Submit job to worker pool
                self._submit_job_to_worker_pool(job, encrypted_credentials)

        self._logger.info(
            f"Scheduled full sync batch {batch.batch_id} with {len(batch.jobs)} jobs",
            extra={
                "batch_id": batch.batch_id,
                "company_id": company_id,
                "provider": provider,
                "domains": [d.value for d in domains],
                "total_jobs": len(batch.jobs),
            },
        )

        return batch

    def schedule_incremental_sync(
        self,
        *,
        company_id: str,
        provider: str,
        domains: list[SyncDomain],
        encrypted_credentials: bytes,
        priority_config: dict[str, JobPriority] | None = None,
    ) -> SyncBatch:
        """Schedule an incremental sync for specified domains."""
        batch = SyncBatch.create(company_id=company_id, provider=provider)

        for domain in domains:
            # Check for existing active checkpoint
            checkpoint = self.checkpoint_repository.find_active_checkpoint(
                company_id=company_id,
                provider=provider,
                domain=domain,
            )

            if checkpoint is None:
                # Create new checkpoint
                checkpoint = self.checkpoint_repository.create_checkpoint(
                    company_id=company_id,
                    provider=provider,
                    domain=domain,
                )
                self.runtime.register_checkpoint_created(domain.value)

            priority = (priority_config or {}).get(domain.value, JobPriority.NORMAL)

            job = SyncJob.create(
                company_id=company_id,
                provider=provider,
                domain=domain,
                priority=priority,
                mode="incremental",
                checkpoint_id=checkpoint.checkpoint_id,
            )

            self.job_repository.create_job(job)
            batch.add_job(job)

            # Submit job to worker pool
            self._submit_job_to_worker_pool(job, encrypted_credentials)

        self._logger.info(
            f"Scheduled incremental sync batch {batch.batch_id} with {len(batch.jobs)} jobs",
            extra={
                "batch_id": batch.batch_id,
                "company_id": company_id,
                "provider": provider,
                "domains": [d.value for d in domains],
                "total_jobs": len(batch.jobs),
            },
        )

        return batch

    def schedule_domain_sync(
        self,
        *,
        company_id: str,
        provider: str,
        domain: SyncDomain,
        encrypted_credentials: bytes,
        mode: str = "incremental",
        window: TimeWindow | None = None,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> SyncJob:
        """Schedule a single domain sync."""
        # Check if there's already a running job for this domain
        if self.job_repository.has_running_jobs(
            company_id=company_id,
            provider=provider,
            domain=domain,
        ):
            raise ValueError(f"Job already running for {domain.value}")

        # Get or create checkpoint
        checkpoint = self.checkpoint_repository.find_active_checkpoint(
            company_id=company_id,
            provider=provider,
            domain=domain,
        )

        if checkpoint is None:
            checkpoint = self.checkpoint_repository.create_checkpoint(
                company_id=company_id,
                provider=provider,
                domain=domain,
                window_start=window.start_date if window else None,
                window_end=window.end_date if window else None,
            )
            self.runtime.register_checkpoint_created(domain.value)

        job = SyncJob.create(
            company_id=company_id,
            provider=provider,
            domain=domain,
            priority=priority,
            window=window,
            mode=mode,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        self.job_repository.create_job(job)
        self._submit_job_to_worker_pool(job, encrypted_credentials)

        self._logger.info(
            f"Scheduled {mode} sync job {job.job_id} for domain {domain.value}",
            extra={
                "job_id": job.job_id,
                "company_id": company_id,
                "provider": provider,
                "domain": domain.value,
                "mode": mode,
            },
        )

        return job

    def pause_job(self, job_id: str) -> None:
        """Pause a running job."""
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")

        job.pause()
        self.job_repository.update_job_status(job_id, JobStatus.PAUSED)

        self._logger.info(f"Job {job_id} paused")

    def resume_job(self, job_id: str, encrypted_credentials: bytes) -> None:
        """Resume a paused job."""
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")

        job.resume()
        self.job_repository.update_job_status(job_id, JobStatus.PENDING)

        # Re-submit to worker pool
        self._submit_job_to_worker_pool(job, encrypted_credentials)

        self._logger.info(f"Job {job_id} resumed")

    def cancel_job(self, job_id: str) -> None:
        """Cancel a job."""
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")

        job.cancel()
        self.job_repository.update_job_status(job_id, JobStatus.CANCELLED)
        self.runtime.register_job_cancelled(job_id, domain=job.domain.value)

        self._logger.info(f"Job {job_id} cancelled")

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get detailed job status."""
        job = self.job_repository.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")

        return job.to_dict()

    def list_active_jobs(self, *, company_id: str | None = None) -> list[dict[str, Any]]:
        """List all active (pending/running) jobs."""
        jobs = self.job_repository.list_jobs(
            company_id=company_id,
            status=JobStatus.RUNNING,
        )
        pending_jobs = self.job_repository.list_jobs(
            company_id=company_id,
            status=JobStatus.PENDING,
        )

        all_jobs = jobs + pending_jobs
        return [job.to_dict() for job in all_jobs]

    def health(self) -> dict[str, Any]:
        """Get orchestrator health status."""
        return {
            "orchestrator": "running",
            "worker_pool": {
                "running": self.worker_pool.is_running(),
                "queue_size": self.worker_pool.queue_size(),
                "max_workers": self.worker_pool.max_workers,
            },
            "runtime": self.runtime.health_snapshot(),
        }

    def _submit_job_to_worker_pool(self, job: SyncJob, encrypted_credentials: bytes) -> None:
        """Submit a job to the worker pool for execution."""

        def execute_job_wrapper() -> None:
            try:
                self.job_dispatcher.execute_job(job, encrypted_credentials)
            except Exception as exc:
                self._logger.error(
                    f"Failed to execute job {job.job_id}: {exc}",
                    exc_info=True,
                )

        self.worker_pool.submit(execute_job_wrapper)
