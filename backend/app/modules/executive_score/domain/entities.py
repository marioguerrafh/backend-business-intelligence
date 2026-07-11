from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ExecutiveScoreAggregate:
    executive_score_id: str
    company_id: str
    period_ref: str
    financial_score: float
    commercial_score: float
    operational_score: float
    inventory_score: float
    executive_score: float
    score_version: str
    calculated_at: datetime
    orchestrator_run_id: str


@dataclass(slots=True, frozen=True)
class ScoreInputs:
    financial_values: tuple[float, ...]
    commercial_values: tuple[float, ...]
    operational_values: tuple[float, ...]
    inventory_values: tuple[float, ...]
    rule_penalty: float
    recommendation_bonus: float
