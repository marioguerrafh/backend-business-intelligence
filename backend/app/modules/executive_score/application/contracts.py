from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CalculateExecutiveScoreCommand:
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    source_event_id: str | None = None
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class CalculateExecutiveScoreResult:
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    financial_score: float
    commercial_score: float
    operational_score: float
    inventory_score: float
    executive_score: float
    published_event_id: str
