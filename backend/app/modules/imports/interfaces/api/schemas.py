from __future__ import annotations

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
