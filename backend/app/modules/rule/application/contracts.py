from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ExecuteRulesCommand:
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    correlation_id: str | None = None
    source_event_id: str | None = None


@dataclass(slots=True, frozen=True)
class ExecuteRulesResult:
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    evaluated_rules: int
    fired_rules: int
    idempotent_hits: int
    published_event_ids: tuple[str, ...]
