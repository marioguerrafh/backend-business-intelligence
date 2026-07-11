from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.recommendation.domain.entities import RecommendationAggregate
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel, RecommendationPublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import KPIResultModel, RecommendationResultModel
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True, frozen=True)
class RuleSignal:
    rule_id: str
    severity: str
    priority: str
    metric_value: float


@dataclass(slots=True)
class SqlAlchemyRecommendationRepository:
    session: Session

    def load_rule_results(self, *, company_id: str, period_ref: str) -> tuple[RuleSignal, ...]:
        rows = self.session.execute(
            select(RuleResultModel).where(
                RuleResultModel.company_id == company_id,
                RuleResultModel.period_ref == period_ref,
            )
        ).scalars().all()
        return tuple(
            RuleSignal(
                rule_id=row.rule_id,
                severity=row.severity,
                priority=row.priority,
                metric_value=float(row.metric_value),
            )
            for row in rows
        )

    def load_kpi_context(self, *, company_id: str, period_ref: str) -> dict[str, object]:
        rows = self.session.execute(
            select(KPIResultModel).where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.period_ref == period_ref,
            )
        ).scalars().all()
        context: dict[str, object] = {
            "open_receivables_over_30d": 0.0,
            "collection_success_rate": 0.6,
            "daily_lost_sales_estimate": 0.0,
            "is_critical_sku": False,
            "business_health_index": 100.0,
            "current_risk_score": 50.0,
            "projected_risk_score": 40.0,
        }
        for row in rows:
            key = row.kpi_id.lower().replace("-", "_")
            context[key] = float(row.value)
            context[f"kpi_{key}"] = float(row.value)

            if row.kpi_id == "FIN-03":
                context["open_receivables_over_30d"] = max(0.0, abs(float(row.value)))
                context["current_risk_score"] = min(100.0, 50.0 + abs(float(row.value)) / 1000.0)
            if row.kpi_id == "EST-02":
                context["daily_lost_sales_estimate"] = max(0.0, float(row.value) * 100.0)
                context["is_critical_sku"] = float(row.value) > 5.0
            if row.kpi_id == "EXE-04":
                context["business_health_index"] = float(row.value)
                context["projected_risk_score"] = max(0.0, 100.0 - float(row.value))
        return context

    def has_recommendation_result(self, *, company_id: str, period_ref: str, recommendation_id: str) -> bool:
        existing = self.session.execute(
            select(RecommendationResultModel).where(
                RecommendationResultModel.company_id == company_id,
                RecommendationResultModel.period_ref == period_ref,
                RecommendationResultModel.recommendation_id == recommendation_id,
            )
        ).scalar_one_or_none()
        return existing is not None

    def save_recommendation_result(self, recommendation: RecommendationAggregate) -> None:
        model = self.session.execute(
            select(RecommendationResultModel).where(
                RecommendationResultModel.company_id == recommendation.company_id,
                RecommendationResultModel.period_ref == recommendation.period_ref,
                RecommendationResultModel.recommendation_id == recommendation.recommendation_id,
            )
        ).scalar_one_or_none()

        payload = {
            "message": recommendation.message,
            "trigger_rule_id": recommendation.trigger_rule_id,
            "group_key": recommendation.group_key,
            "impact_score": recommendation.impact_score,
            "urgency_score": recommendation.urgency_score,
            "effort_score": recommendation.effort_score,
            "expected_impact_value": recommendation.expected_impact_value,
            "expected_impact_unit": recommendation.expected_impact_unit,
            "expected_impact_horizon": recommendation.expected_impact_horizon,
            "confidence_score": recommendation.confidence_score,
            "action_playbook": list(recommendation.action_playbook),
            "orchestrator_run_id": recommendation.orchestrator_run_id,
        }

        if model is None:
            model = RecommendationResultModel(
                recommendation_result_id=recommendation.recommendation_result_id,
                company_id=recommendation.company_id,
                period_ref=recommendation.period_ref,
                recommendation_id=recommendation.recommendation_id,
                title=recommendation.title,
                rank_score=recommendation.rank_score,
                expected_impact_json=payload,
                owner_role=recommendation.owner_role,
                sla_target=recommendation.sla_target,
                generated_at=recommendation.generated_at,
            )
            self.session.add(model)
        else:
            model.title = recommendation.title
            model.rank_score = recommendation.rank_score
            model.expected_impact_json = payload
            model.owner_role = recommendation.owner_role
            model.sla_target = recommendation.sla_target
            model.generated_at = recommendation.generated_at

        self.session.flush()

    def add_audit(
        self,
        *,
        company_id: str,
        period_ref: str,
        recommendation_id: str,
        trigger_rule_id: str,
        status: str,
        details: dict[str, object],
        orchestrator_run_id: str,
    ) -> None:
        self.session.add(
            RecommendationAuditLogModel(
                audit_log_id=f"reca_{uuid4().hex[:16]}",
                company_id=company_id,
                period_ref=period_ref,
                recommendation_id=recommendation_id,
                trigger_rule_id=trigger_rule_id,
                status=status,
                details_json=json.dumps(details),
                orchestrator_run_id=orchestrator_run_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_recommendation_generated(self, *, payload: dict[str, object]) -> str:
        event = IntegrationEvent(topic="recommendation.generated.v1", payload=payload)
        self.session.add(
            RecommendationPublishedEventModel(
                event_id=event.event_id,
                company_id=str(payload["company_id"]),
                period_ref=str(payload["period_ref"]),
                recommendation_id=str(payload["recommendation_id"]),
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id
