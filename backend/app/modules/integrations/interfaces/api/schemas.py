from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConnectIntegrationRequest(BaseModel):
    provider: Literal[
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
    credentials: dict[str, Any] = Field(default_factory=dict)


class IntegrationConnectionResponse(BaseModel):
    id: str
    company_id: str
    provider: str
    status: str
    enabled: bool
    last_sync: datetime | None
    last_success_sync: datetime | None
    created_at: datetime
    updated_at: datetime


class IntegrationSyncJobResponse(BaseModel):
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
