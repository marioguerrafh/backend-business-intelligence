"""API schemas for synchronization endpoints."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class TimeWindowResponse(BaseModel):
    """Response schema for time window."""

    window_id: str
    start_date: date
    end_date: date
    days: int


class SyncJobResponse(BaseModel):
    """Response schema for sync job."""

    job_id: str
    company_id: str
    provider: str
    domain: str
    priority: str
    status: str
    mode: str
    window: TimeWindowResponse | None = None
    checkpoint_id: str | None = None
    retry_count: int
    max_retries: int
    records_read: int
    records_imported: int
    records_failed: int
    pages_processed: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    created_at: datetime
    updated_at: datetime


class CheckpointResponse(BaseModel):
    """Response schema for checkpoint."""

    checkpoint_id: str
    company_id: str
    provider: str
    domain: str
    status: str
    last_page: int | None = None
    last_cursor: str | None = None
    last_success_sync: datetime | None = None
    last_processed_record: str | None = None
    last_window_start: date | None = None
    last_window_end: date | None = None
    created_at: datetime
    updated_at: datetime


class ScheduleFullSyncRequest(BaseModel):
    """Request schema for scheduling full sync."""

    company_id: str = Field(..., description="Company ID")
    provider: str = Field(..., description="Provider name (e.g., 'omie')")
    domains: list[str] = Field(..., description="List of domains to sync")
    window_config: dict[str, int] = Field(
        default_factory=dict,
        description="Domain-specific window configurations (domain -> days)",
    )
    priority_config: dict[str, str] = Field(
        default_factory=dict,
        description="Domain-specific priorities",
    )


class ScheduleIncrementalSyncRequest(BaseModel):
    """Request schema for scheduling incremental sync."""

    company_id: str = Field(..., description="Company ID")
    provider: str = Field(..., description="Provider name")
    domains: list[str] = Field(..., description="List of domains to sync")
    priority_config: dict[str, str] = Field(
        default_factory=dict,
        description="Domain-specific priorities",
    )


class ScheduleDomainSyncRequest(BaseModel):
    """Request schema for scheduling domain sync."""

    company_id: str = Field(..., description="Company ID")
    provider: str = Field(..., description="Provider name")
    domain: str = Field(..., description="Domain to sync")
    mode: str = Field(default="incremental", description="Sync mode: incremental or full")
    window_start: date | None = Field(None, description="Window start date")
    window_end: date | None = Field(None, description="Window end date")
    priority: str = Field(default="normal", description="Job priority")


class BatchResponse(BaseModel):
    """Response schema for sync batch."""

    batch_id: str
    company_id: str
    provider: str
    total_jobs: int
    jobs: list[SyncJobResponse]
    pipeline_execution_required: bool
    created_at: datetime


class OrchestratorHealthResponse(BaseModel):
    """Response schema for orchestrator health."""

    orchestrator: str
    worker_pool: dict
    runtime: dict


class ScheduleStatusResponse(BaseModel):
    """Response schema for schedule status."""

    running: bool
    schedules: dict


class ListJobsResponse(BaseModel):
    """Response schema for listing jobs."""

    total: int
    jobs: list[SyncJobResponse]


class ListCheckpointsResponse(BaseModel):
    """Response schema for listing checkpoints."""

    total: int
    checkpoints: list[CheckpointResponse]
