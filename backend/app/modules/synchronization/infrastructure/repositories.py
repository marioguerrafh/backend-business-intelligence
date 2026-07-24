"""Repository for synchronization checkpoints and jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.synchronization.domain.entities import SyncCheckpoint, SyncJob, TimeWindow
from app.modules.synchronization.domain.value_objects import CheckpointStatus, JobPriority, JobStatus, SyncDomain


@dataclass(slots=True)
class CheckpointRepository:
    """Repository for managing synchronization checkpoints."""

    session: Session

    def create_checkpoint(
        self,
        *,
        company_id: str,
        provider: str,
        domain: SyncDomain,
        window_start: date | None = None,
        window_end: date | None = None,
    ) -> SyncCheckpoint:
        """Create a new checkpoint."""
        checkpoint_id = str(uuid4())
        now = datetime.utcnow()

        stmt = text("""
            INSERT INTO sync_checkpoints (
                checkpoint_id, company_id, provider, domain, status,
                last_window_start, last_window_end, created_at, updated_at
            ) VALUES (
                :checkpoint_id, :company_id, :provider, :domain, :status,
                :window_start, :window_end, :created_at, :updated_at
            )
        """)

        self.session.execute(
            stmt,
            {
                "checkpoint_id": checkpoint_id,
                "company_id": company_id,
                "provider": provider,
                "domain": domain.value,
                "status": CheckpointStatus.ACTIVE.value,
                "window_start": window_start,
                "window_end": window_end,
                "created_at": now,
                "updated_at": now,
            },
        )
        self.session.flush()

        return SyncCheckpoint(
            checkpoint_id=checkpoint_id,
            company_id=company_id,
            provider=provider,
            domain=domain,
            status=CheckpointStatus.ACTIVE,
            last_window_start=window_start,
            last_window_end=window_end,
            created_at=now,
            updated_at=now,
        )

    def get_checkpoint(self, checkpoint_id: str) -> SyncCheckpoint | None:
        """Get checkpoint by ID."""
        stmt = text("""
            SELECT 
                checkpoint_id, company_id, provider, domain, status,
                last_page, last_cursor, last_success_sync, last_processed_record,
                last_window_start, last_window_end, metadata, created_at, updated_at
            FROM sync_checkpoints
            WHERE checkpoint_id = :checkpoint_id
        """)

        row = self.session.execute(stmt, {"checkpoint_id": checkpoint_id}).fetchone()
        if row is None:
            return None

        return self._row_to_checkpoint(row)

    def find_active_checkpoint(
        self,
        *,
        company_id: str,
        provider: str,
        domain: SyncDomain,
    ) -> SyncCheckpoint | None:
        """Find active checkpoint for company/provider/domain."""
        stmt = text("""
            SELECT 
                checkpoint_id, company_id, provider, domain, status,
                last_page, last_cursor, last_success_sync, last_processed_record,
                last_window_start, last_window_end, metadata, created_at, updated_at
            FROM sync_checkpoints
            WHERE company_id = :company_id
              AND provider = :provider
              AND domain = :domain
              AND status = :status
            ORDER BY updated_at DESC
            LIMIT 1
        """)

        row = self.session.execute(
            stmt,
            {
                "company_id": company_id,
                "provider": provider,
                "domain": domain.value,
                "status": CheckpointStatus.ACTIVE.value,
            },
        ).fetchone()

        if row is None:
            return None

        return self._row_to_checkpoint(row)

    def update_checkpoint_progress(
        self,
        checkpoint_id: str,
        *,
        page: int | None = None,
        cursor: str | None = None,
        processed_record: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update checkpoint progress."""
        updates = ["updated_at = :updated_at"]
        params: dict[str, Any] = {
            "checkpoint_id": checkpoint_id,
            "updated_at": datetime.utcnow(),
        }

        if page is not None:
            updates.append("last_page = :last_page")
            params["last_page"] = page

        if cursor is not None:
            updates.append("last_cursor = :last_cursor")
            params["last_cursor"] = cursor

        if processed_record is not None:
            updates.append("last_processed_record = :last_processed_record")
            params["last_processed_record"] = processed_record

        if metadata is not None:
            updates.append("metadata = :metadata")
            params["metadata"] = json.dumps(metadata)

        stmt = text(f"""
            UPDATE sync_checkpoints
            SET {', '.join(updates)}
            WHERE checkpoint_id = :checkpoint_id
        """)

        self.session.execute(stmt, params)
        self.session.flush()

    def mark_checkpoint_completed(self, checkpoint_id: str) -> None:
        """Mark checkpoint as completed."""
        stmt = text("""
            UPDATE sync_checkpoints
            SET status = :status,
                last_success_sync = :last_success_sync,
                updated_at = :updated_at
            WHERE checkpoint_id = :checkpoint_id
        """)

        now = datetime.utcnow()
        self.session.execute(
            stmt,
            {
                "checkpoint_id": checkpoint_id,
                "status": CheckpointStatus.COMPLETED.value,
                "last_success_sync": now,
                "updated_at": now,
            },
        )
        self.session.flush()

    def mark_checkpoint_failed(self, checkpoint_id: str) -> None:
        """Mark checkpoint as failed."""
        stmt = text("""
            UPDATE sync_checkpoints
            SET status = :status, updated_at = :updated_at
            WHERE checkpoint_id = :checkpoint_id
        """)

        self.session.execute(
            stmt,
            {
                "checkpoint_id": checkpoint_id,
                "status": CheckpointStatus.FAILED.value,
                "updated_at": datetime.utcnow(),
            },
        )
        self.session.flush()

    def list_checkpoints(
        self,
        *,
        company_id: str,
        provider: str | None = None,
        domain: SyncDomain | None = None,
        status: CheckpointStatus | None = None,
        limit: int = 100,
    ) -> list[SyncCheckpoint]:
        """List checkpoints with optional filters."""
        conditions = ["company_id = :company_id"]
        params: dict[str, Any] = {"company_id": company_id, "limit": limit}

        if provider:
            conditions.append("provider = :provider")
            params["provider"] = provider

        if domain:
            conditions.append("domain = :domain")
            params["domain"] = domain.value

        if status:
            conditions.append("status = :status")
            params["status"] = status.value

        where_clause = " AND ".join(conditions)

        stmt = text(f"""
            SELECT 
                checkpoint_id, company_id, provider, domain, status,
                last_page, last_cursor, last_success_sync, last_processed_record,
                last_window_start, last_window_end, metadata, created_at, updated_at
            FROM sync_checkpoints
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT :limit
        """)

        rows = self.session.execute(stmt, params).fetchall()
        return [self._row_to_checkpoint(row) for row in rows]

    @staticmethod
    def _row_to_checkpoint(row: Any) -> SyncCheckpoint:
        """Convert database row to SyncCheckpoint entity."""
        metadata = {}
        if row.metadata:
            try:
                metadata = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        return SyncCheckpoint(
            checkpoint_id=row.checkpoint_id,
            company_id=row.company_id,
            provider=row.provider,
            domain=SyncDomain(row.domain),
            status=CheckpointStatus(row.status),
            last_page=row.last_page,
            last_cursor=row.last_cursor,
            last_success_sync=row.last_success_sync,
            last_processed_record=row.last_processed_record,
            last_window_start=row.last_window_start,
            last_window_end=row.last_window_end,
            metadata=metadata,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


@dataclass(slots=True)
class JobRepository:
    """Repository for managing synchronization jobs."""

    session: Session

    def create_job(self, job: SyncJob) -> None:
        """Persist a new job."""
        stmt = text("""
            INSERT INTO sync_jobs (
                job_id, company_id, provider, domain, priority, status, mode,
                checkpoint_id, window_start, window_end, window_id,
                retry_count, max_retries, metadata, created_at, updated_at
            ) VALUES (
                :job_id, :company_id, :provider, :domain, :priority, :status, :mode,
                :checkpoint_id, :window_start, :window_end, :window_id,
                :retry_count, :max_retries, :metadata, :created_at, :updated_at
            )
        """)

        self.session.execute(
            stmt,
            {
                "job_id": job.job_id,
                "company_id": job.company_id,
                "provider": job.provider,
                "domain": job.domain.value,
                "priority": job.priority.value,
                "status": job.status.value,
                "mode": job.mode,
                "checkpoint_id": job.checkpoint_id,
                "window_start": job.window.start_date if job.window else None,
                "window_end": job.window.end_date if job.window else None,
                "window_id": job.window.window_id if job.window else None,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "metadata": json.dumps(job.metadata),
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            },
        )
        self.session.flush()

    def get_job(self, job_id: str) -> SyncJob | None:
        """Get job by ID."""
        stmt = text("""
            SELECT 
                job_id, company_id, provider, domain, priority, status, mode,
                checkpoint_id, window_start, window_end, window_id,
                retry_count, max_retries, records_read, records_imported, records_failed,
                pages_processed, started_at, completed_at, failed_at, error_message,
                metadata, created_at, updated_at
            FROM sync_jobs
            WHERE job_id = :job_id
        """)

        row = self.session.execute(stmt, {"job_id": job_id}).fetchone()
        if row is None:
            return None

        return self._row_to_job(row)

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        **kwargs: Any,
    ) -> None:
        """Update job status and optional fields."""
        updates = ["status = :status", "updated_at = :updated_at"]
        params: dict[str, Any] = {
            "job_id": job_id,
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if "started_at" in kwargs:
            updates.append("started_at = :started_at")
            params["started_at"] = kwargs["started_at"]

        if "completed_at" in kwargs:
            updates.append("completed_at = :completed_at")
            params["completed_at"] = kwargs["completed_at"]

        if "failed_at" in kwargs:
            updates.append("failed_at = :failed_at")
            params["failed_at"] = kwargs["failed_at"]

        if "error_message" in kwargs:
            updates.append("error_message = :error_message")
            params["error_message"] = kwargs["error_message"]

        if "retry_count" in kwargs:
            updates.append("retry_count = :retry_count")
            params["retry_count"] = kwargs["retry_count"]

        if "records_read" in kwargs:
            updates.append("records_read = :records_read")
            params["records_read"] = kwargs["records_read"]

        if "records_imported" in kwargs:
            updates.append("records_imported = :records_imported")
            params["records_imported"] = kwargs["records_imported"]

        if "records_failed" in kwargs:
            updates.append("records_failed = :records_failed")
            params["records_failed"] = kwargs["records_failed"]

        if "pages_processed" in kwargs:
            updates.append("pages_processed = :pages_processed")
            params["pages_processed"] = kwargs["pages_processed"]

        stmt = text(f"""
            UPDATE sync_jobs
            SET {', '.join(updates)}
            WHERE job_id = :job_id
        """)

        self.session.execute(stmt, params)
        self.session.flush()

    def list_jobs(
        self,
        *,
        company_id: str | None = None,
        provider: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[SyncJob]:
        """List jobs with optional filters."""
        conditions = []
        params: dict[str, Any] = {"limit": limit}

        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id

        if provider:
            conditions.append("provider = :provider")
            params["provider"] = provider

        if status:
            conditions.append("status = :status")
            params["status"] = status.value

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        stmt = text(f"""
            SELECT 
                job_id, company_id, provider, domain, priority, status, mode,
                checkpoint_id, window_start, window_end, window_id,
                retry_count, max_retries, records_read, records_imported, records_failed,
                pages_processed, started_at, completed_at, failed_at, error_message,
                metadata, created_at, updated_at
            FROM sync_jobs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        rows = self.session.execute(stmt, params).fetchall()
        return [self._row_to_job(row) for row in rows]

    def list_pending_jobs(self, *, company_id: str | None = None) -> list[SyncJob]:
        """List all pending jobs, optionally filtered by company."""
        conditions = ["status = :status"]
        params: dict[str, Any] = {"status": JobStatus.PENDING.value}

        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id

        where_clause = " AND ".join(conditions)

        stmt = text(f"""
            SELECT 
                job_id, company_id, provider, domain, priority, status, mode,
                checkpoint_id, window_start, window_end, window_id,
                retry_count, max_retries, records_read, records_imported, records_failed,
                pages_processed, started_at, completed_at, failed_at, error_message,
                metadata, created_at, updated_at
            FROM sync_jobs
            WHERE {where_clause}
            ORDER BY 
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                created_at ASC
        """)

        rows = self.session.execute(stmt, params).fetchall()
        return [self._row_to_job(row) for row in rows]

    def has_running_jobs(self, *, company_id: str, provider: str, domain: SyncDomain) -> bool:
        """Check if there are running jobs for the given combination."""
        stmt = text("""
            SELECT COUNT(*) as count
            FROM sync_jobs
            WHERE company_id = :company_id
              AND provider = :provider
              AND domain = :domain
              AND status IN ('running', 'pending')
        """)

        row = self.session.execute(
            stmt,
            {
                "company_id": company_id,
                "provider": provider,
                "domain": domain.value,
            },
        ).fetchone()

        return row.count > 0 if row else False

    @staticmethod
    def _row_to_job(row: Any) -> SyncJob:
        """Convert database row to SyncJob entity."""
        metadata = {}
        if row.metadata:
            try:
                metadata = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        window = None
        if row.window_start and row.window_end:
            window = TimeWindow(
                start_date=row.window_start,
                end_date=row.window_end,
                window_id=row.window_id or str(uuid4()),
            )

        return SyncJob(
            job_id=row.job_id,
            company_id=row.company_id,
            provider=row.provider,
            domain=SyncDomain(row.domain),
            priority=JobPriority(row.priority),
            status=JobStatus(row.status),
            mode=row.mode,
            checkpoint_id=row.checkpoint_id,
            window=window,
            retry_count=row.retry_count,
            max_retries=row.max_retries,
            records_read=row.records_read or 0,
            records_imported=row.records_imported or 0,
            records_failed=row.records_failed or 0,
            pages_processed=row.pages_processed or 0,
            started_at=row.started_at,
            completed_at=row.completed_at,
            failed_at=row.failed_at,
            error_message=row.error_message,
            metadata=metadata,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
