from __future__ import annotations

from dataclasses import dataclass

from app.modules.recommendation.domain.entities import RecommendationAggregate


@dataclass(slots=True)
class RecommendationPublisher:
    repository: object

    def publish(self, recommendation: RecommendationAggregate, source_event_id: str | None) -> str:
        return self.repository.publish_recommendation_generated(
            payload={
                "company_id": recommendation.company_id,
                "period_ref": recommendation.period_ref,
                "recommendation_id": recommendation.recommendation_id,
                "trigger_rule_id": recommendation.trigger_rule_id,
                "rank_score": recommendation.rank_score,
                "impact_score": recommendation.impact_score,
                "urgency_score": recommendation.urgency_score,
                "effort_score": recommendation.effort_score,
                "owner_role": recommendation.owner_role,
                "sla_target": recommendation.sla_target,
                "orchestrator_run_id": recommendation.orchestrator_run_id,
                "source_event_id": source_event_id,
            }
        )
