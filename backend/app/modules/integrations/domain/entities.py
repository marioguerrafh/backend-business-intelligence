from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class IntegrationConnection:
    id: str
    company_id: str
    provider: str
    status: str
    enabled: bool
    last_sync: datetime | None
    last_success_sync: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class IntegrationSyncJob:
    job_id: str
    provider: str
    company_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    records_read: int
    records_imported: int
    records_failed: int
    pipeline_run_id: str | None
