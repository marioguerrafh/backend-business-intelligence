from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StartPipelineRequest(BaseModel):
    company_id: str = Field(min_length=1)
    import_job_id: str = Field(min_length=1)
    template: Literal[
        "customers",
        "products",
        "sales",
        "cashflow",
        "financial",
        "balance_sheet",
        "income_statement",
        "accounts_receivable",
        "accounts_payable",
        "inventory",
        "hr",
    ]
    source_system: str = Field(min_length=1)
    ingest_event_id: str | None = None
    correlation_id: str | None = None
    allow_retry: bool = False


class PipelineRunResponse(BaseModel):
    pipeline_run_id: str
    company_id: str
    import_job_id: str
    template: str
    status: str
    progress: int
    current_step: str | None
    started_at: datetime
    finished_at: datetime | None
    correlation_id: str | None
    reused_existing_run: bool
    retry_of_pipeline_run_id: str | None
    attempt: int


class PipelineStepResponse(BaseModel):
    step_id: str
    pipeline_run_id: str
    step_name: str
    step_order: int
    status: str
    duration_ms: int | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None


class PipelineLogResponse(BaseModel):
    log_id: str
    pipeline_run_id: str
    company_id: str
    step_name: str | None
    status: str
    duration_ms: int | None
    message: str
    error_message: str | None
    correlation_id: str | None
    created_at: datetime
