from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class RecommendationDefinition:
    recommendation_id: str
    name: str
    trigger_rule_id: str
    applicability_conditions: tuple[str, ...]
    expected_impact_formula: str
    expected_impact_unit: str
    impact_horizon: str
    effort_level: str
    confidence_score: float
    owner_role: str
    sla_target: str
    message_template: str
    action_playbook: tuple[str, ...]
    enabled: bool


@dataclass(slots=True, frozen=True)
class RecommendationAggregate:
    recommendation_result_id: str
    recommendation_id: str
    company_id: str
    period_ref: str
    trigger_rule_id: str
    title: str
    message: str
    group_key: str
    impact_score: float
    urgency_score: float
    effort_score: float
    rank_score: float
    expected_impact_value: float
    expected_impact_unit: str
    expected_impact_horizon: str
    owner_role: str
    sla_target: str
    confidence_score: float
    action_playbook: tuple[str, ...]
    orchestrator_run_id: str
    generated_at: datetime
