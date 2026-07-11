from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class PipelineStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PipelineStageName(StrEnum):
    KPI_ORCHESTRATOR = "KPI Orchestrator"
    RULE_ENGINE = "Rule Engine"
    RECOMMENDATION_ENGINE = "Recommendation Engine"
    INSIGHT_ENGINE = "Insight Engine"
    EXECUTIVE_SCORE_ENGINE = "Executive Score Engine"
    SUMMARY_ENGINE = "Summary Engine"


@dataclass(slots=True)
class PipelineStage:
    step_id: str
    run_id: str
    name: PipelineStageName
    stage_order: int
    status: PipelineStatus = PipelineStatus.PENDING
    duration_ms: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


@dataclass(slots=True)
class PipelineRun:
    pipeline_run_id: str
    company_id: str
    import_job_id: str
    template: str
    status: PipelineStatus
    progress: int
    current_step: str | None
    started_at: datetime
    finished_at: datetime | None
    correlation_id: str | None
    retry_of_pipeline_run_id: str | None = None
    attempt: int = 1


@dataclass(slots=True)
class PipelineAggregate:
    run: PipelineRun
    stages: list[PipelineStage] = field(default_factory=list)
