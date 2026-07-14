from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


ProviderType = Literal[
    "omie",
    "conta_azul",
    "tiny",
    "bling",
    "sap",
    "totvs",
    "senior",
    "sankhya",
    "oracle",
    "dynamics",
]


SyncMode = Literal["full", "incremental"]


@dataclass(slots=True, frozen=True)
class ConnectIntegrationCommand:
    company_id: str
    provider: ProviderType
    credentials: dict[str, Any]


@dataclass(slots=True, frozen=True)
class RunIntegrationSyncCommand:
    company_id: str
    integration_id: str
    mode: SyncMode


@dataclass(slots=True, frozen=True)
class IntegrationConnectionResult:
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
class IntegrationSyncJobResult:
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
