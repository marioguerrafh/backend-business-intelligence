from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ImportInconsistencyResponse(BaseModel):
    row_number: int
    field: str
    message: str
    raw_value: str | None


class ImportCsvResponse(BaseModel):
    job_id: str
    template: Literal["customers", "products", "sales", "financial"]
    status: Literal["success", "partial", "failed"]
    total_rows: int
    imported_rows: int
    failed_rows: int
    ingest_event_id: str | None
    inconsistencies: list[ImportInconsistencyResponse]


class ImportJobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: str | None
    started_at: datetime
    estimated_remaining_seconds: int
    summary_updated: bool
