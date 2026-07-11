from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.recommendation.domain.entities import RecommendationAggregate, RecommendationDefinition


@dataclass(slots=True)
class RecommendationBuilder:
    def build(
        self,
        *,
        definition: RecommendationDefinition,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        trigger_rule_id: str,
        expected_impact_value: float,
        impact_score: float,
        urgency_score: float,
        effort_score: float,
        rank_score: float,
    ) -> RecommendationAggregate:
        message = definition.message_template.replace(
            "{expected_impact_value}", f"{expected_impact_value:.2f}"
        ).replace("{impact_horizon}", definition.impact_horizon)

        return RecommendationAggregate(
            recommendation_result_id=f"rrec_{uuid4().hex[:16]}",
            recommendation_id=definition.recommendation_id,
            company_id=company_id,
            period_ref=period_ref,
            trigger_rule_id=trigger_rule_id,
            title=definition.name,
            message=message,
            group_key=f"{trigger_rule_id}:{definition.owner_role}",
            impact_score=impact_score,
            urgency_score=urgency_score,
            effort_score=effort_score,
            rank_score=rank_score,
            expected_impact_value=expected_impact_value,
            expected_impact_unit=definition.expected_impact_unit,
            expected_impact_horizon=definition.impact_horizon,
            owner_role=definition.owner_role,
            sla_target=definition.sla_target,
            confidence_score=definition.confidence_score,
            action_playbook=definition.action_playbook,
            orchestrator_run_id=orchestrator_run_id,
            generated_at=datetime.now(timezone.utc),
        )
