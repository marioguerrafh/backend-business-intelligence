from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


PipelineStageStatus = Literal["PENDING", "RUNNING", "SUCCESS", "FAILED", "SKIPPED"]


@dataclass(slots=True, frozen=True)
class StartPipelineCommand:
    company_id: str
    import_job_id: str
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
    source_system: str
    ingest_event_id: str | None = None
    correlation_id: str | None = None
    allow_retry: bool = False


@dataclass(slots=True, frozen=True)
class PipelineRunResult:
    pipeline_run_id: str
    company_id: str
    import_job_id: str
    template: str
    status: PipelineStageStatus
    progress: int
    current_step: str | None
    started_at: datetime
    finished_at: datetime | None
    correlation_id: str | None
    reused_existing_run: bool = False
    retry_of_pipeline_run_id: str | None = None
    attempt: int = 1


@dataclass(slots=True, frozen=True)
class PipelineStepResult:
    step_id: str
    pipeline_run_id: str
    step_name: str
    step_order: int
    status: PipelineStageStatus
    duration_ms: int | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None


@dataclass(slots=True, frozen=True)
class PipelineLogResult:
    log_id: str
    pipeline_run_id: str
    company_id: str
    step_name: str | None
    status: PipelineStageStatus
    duration_ms: int | None
    message: str
    error_message: str | None
    correlation_id: str | None
    created_at: datetime


@dataclass(slots=True, frozen=True)
class ImportJobProgressResult:
    job_id: str
    status: str
    progress: int
    current_step: str | None
    started_at: datetime
    estimated_remaining_seconds: int
    summary_updated: bool
