"""Domain entities for synchronization orchestration."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from app.modules.synchronization.domain.value_objects import CheckpointStatus, JobPriority, JobStatus, SyncDomain


@dataclass(slots=True)
class TimeWindow:
    """Represents a time window for synchronization."""

    start_date: date
    end_date: date
    window_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")

    @property
    def days(self) -> int:
        """Calculate number of days in the window."""
        return (self.end_date - self.start_date).days + 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "window_id": self.window_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "days": self.days,
        }


@dataclass(slots=True)
class SyncCheckpoint:
    """Checkpoint for resumable synchronization."""

    checkpoint_id: str
    company_id: str
    provider: str
    domain: SyncDomain
    status: CheckpointStatus
    last_page: int | None = None
    last_cursor: str | None = None
    last_success_sync: datetime | None = None
    last_processed_record: str | None = None
    last_window_start: date | None = None
    last_window_end: date | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_completed(self) -> None:
        """Mark checkpoint as completed."""
        self.status = CheckpointStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark checkpoint as failed."""
        self.status = CheckpointStatus.FAILED
        self.updated_at = datetime.utcnow()

    def update_progress(
        self,
        *,
        page: int | None = None,
        cursor: str | None = None,
        processed_record: str | None = None,
    ) -> None:
        """Update checkpoint progress."""
        if page is not None:
            self.last_page = page
        if cursor is not None:
            self.last_cursor = cursor
        if processed_record is not None:
            self.last_processed_record = processed_record
        self.updated_at = datetime.utcnow()


@dataclass(slots=True)
class SyncJob:
    """Synchronization job for a specific domain."""

    job_id: str
    company_id: str
    provider: str
    domain: SyncDomain
    priority: JobPriority
    status: JobStatus
    window: TimeWindow | None = None
    checkpoint_id: str | None = None
    mode: str = "incremental"  # incremental or full
    retry_count: int = 0
    max_retries: int = 3
    records_read: int = 0
    records_imported: int = 0
    records_failed: int = 0
    pages_processed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        *,
        company_id: str,
        provider: str,
        domain: SyncDomain,
        priority: JobPriority = JobPriority.NORMAL,
        window: TimeWindow | None = None,
        mode: str = "incremental",
        checkpoint_id: str | None = None,
    ) -> SyncJob:
        """Factory method to create a new sync job."""
        return cls(
            job_id=str(uuid4()),
            company_id=company_id,
            provider=provider,
            domain=domain,
            priority=priority,
            status=JobStatus.PENDING,
            window=window,
            mode=mode,
            checkpoint_id=checkpoint_id,
        )

    def start(self) -> None:
        """Mark job as running."""
        if self.status != JobStatus.PENDING:
            raise ValueError(f"Cannot start job in status {self.status}")
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, *, records_read: int, records_imported: int, records_failed: int, pages_processed: int) -> None:
        """Mark job as completed."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(f"Cannot complete job in status {self.status}")
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.records_read = records_read
        self.records_imported = records_imported
        self.records_failed = records_failed
        self.pages_processed = pages_processed

    def fail(self, error_message: str) -> None:
        """Mark job as failed."""
        if self.status not in {JobStatus.RUNNING, JobStatus.PENDING}:
            raise ValueError(f"Cannot fail job in status {self.status}")
        self.status = JobStatus.FAILED
        self.failed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1

    def pause(self) -> None:
        """Pause a running job."""
        if self.status != JobStatus.RUNNING:
            raise ValueError(f"Cannot pause job in status {self.status}")
        self.status = JobStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """Resume a paused job."""
        if self.status != JobStatus.PAUSED:
            raise ValueError(f"Cannot resume job in status {self.status}")
        self.status = JobStatus.PENDING
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel a job."""
        if self.status in {JobStatus.COMPLETED, JobStatus.CANCELLED}:
            raise ValueError(f"Cannot cancel job in status {self.status}")
        self.status = JobStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries

    @property
    def duration_seconds(self) -> float | None:
        """Calculate job duration in seconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or self.failed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary representation."""
        return {
            "job_id": self.job_id,
            "company_id": self.company_id,
            "provider": self.provider,
            "domain": self.domain.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "mode": self.mode,
            "window": self.window.to_dict() if self.window else None,
            "checkpoint_id": self.checkpoint_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "records_read": self.records_read,
            "records_imported": self.records_imported,
            "records_failed": self.records_failed,
            "pages_processed": self.pages_processed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(slots=True)
class SyncBatch:
    """Represents a batch of sync jobs to be executed together."""

    batch_id: str
    company_id: str
    provider: str
    jobs: list[SyncJob] = field(default_factory=list)
    pipeline_execution_required: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, *, company_id: str, provider: str) -> SyncBatch:
        """Factory method to create a new batch."""
        return cls(
            batch_id=str(uuid4()),
            company_id=company_id,
            provider=provider,
        )

    def add_job(self, job: SyncJob) -> None:
        """Add a job to the batch."""
        if job.company_id != self.company_id:
            raise ValueError("Job company_id does not match batch company_id")
        if job.provider != self.provider:
            raise ValueError("Job provider does not match batch provider")
        self.jobs.append(job)

    def all_completed(self) -> bool:
        """Check if all jobs in batch are completed."""
        return all(job.status == JobStatus.COMPLETED for job in self.jobs)

    def has_failures(self) -> bool:
        """Check if any job in batch has failed."""
        return any(job.status == JobStatus.FAILED for job in self.jobs)

    def total_records_imported(self) -> int:
        """Calculate total records imported across all jobs."""
        return sum(job.records_imported for job in self.jobs)
