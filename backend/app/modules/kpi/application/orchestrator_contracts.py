from __future__ import annotations

from dataclasses import dataclass

from app.modules.imports.application.contracts import ImportTemplate


@dataclass(slots=True, frozen=True)
class IngestCompletedEvent:
    company_id: str
    import_job_id: str
    template: ImportTemplate
    source_system: str
    event_id: str | None = None
    orchestrator_run_id: str | None = None
    period_ref: str | None = None
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class PeriodRunResult:
    period_ref: str
    orchestrator_run_id: str
    status: str
    recalculated_count: int
    failed_count: int
    idempotent_hit: bool
    published_event_ids: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class OrchestratorResult:
    source_event_topic: str
    source_event_id: str | None
    company_id: str
    import_job_id: str
    periods: tuple[PeriodRunResult, ...]
