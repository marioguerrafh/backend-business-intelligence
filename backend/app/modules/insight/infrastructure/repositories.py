from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.insight.domain.entities import InsightAggregate
from app.modules.insight.infrastructure.models import InsightAuditLogModel, InsightPublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import InsightResultModel, KPIResultModel, RecommendationResultModel
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class SqlAlchemyInsightRepository:
    session: Session

    def load_kpi_context(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(KPIResultModel).where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.period_ref == period_ref,
            )
        ).scalars().all()
        return {row.kpi_id.replace("-", "_"): float(row.value) for row in rows}

    def load_fired_rule_ids(self, *, company_id: str, period_ref: str) -> tuple[str, ...]:
        rows = self.session.execute(
            select(RuleResultModel.rule_id).where(
                RuleResultModel.company_id == company_id,
                RuleResultModel.period_ref == period_ref,
            )
        ).all()
        return tuple(str(row[0]) for row in rows)

    def load_top_recommendation_ids(self, *, company_id: str, period_ref: str, limit: int = 3) -> tuple[str, ...]:
        rows = self.session.execute(
            select(RecommendationResultModel)
            .where(
                RecommendationResultModel.company_id == company_id,
                RecommendationResultModel.period_ref == period_ref,
            )
            .order_by(RecommendationResultModel.rank_score.desc())
            .limit(limit)
        ).scalars().all()
        return tuple(item.recommendation_id for item in rows)

    def has_insight(self, *, company_id: str, period_ref: str, insight_type: str) -> bool:
        model = self.session.execute(
            select(InsightResultModel).where(
                InsightResultModel.company_id == company_id,
                InsightResultModel.period_ref == period_ref,
                InsightResultModel.insight_type == insight_type,
            )
        ).scalar_one_or_none()
        return model is not None

    def save_insight(self, insight: InsightAggregate) -> None:
        model = self.session.execute(
            select(InsightResultModel).where(
                InsightResultModel.company_id == insight.company_id,
                InsightResultModel.period_ref == insight.period_ref,
                InsightResultModel.insight_type == insight.insight_type,
            )
        ).scalar_one_or_none()

        evidence = {
            **insight.evidence,
            "prompt_id": insight.prompt_id,
            "orchestrator_run_id": insight.orchestrator_run_id,
        }

        if model is None:
            model = InsightResultModel(
                insight_result_id=insight.insight_result_id,
                company_id=insight.company_id,
                period_ref=insight.period_ref,
                insight_type=insight.insight_type,
                statement=insight.statement,
                evidence_json=evidence,
                generated_at=insight.generated_at,
            )
            self.session.add(model)
        else:
            model.statement = insight.statement
            model.evidence_json = evidence
            model.generated_at = insight.generated_at

        self.session.flush()

    def add_audit(
        self,
        *,
        company_id: str,
        period_ref: str,
        insight_type: str,
        status: str,
        details: dict[str, object],
        orchestrator_run_id: str,
    ) -> None:
        self.session.add(
            InsightAuditLogModel(
                audit_log_id=f"inad_{uuid4().hex[:16]}",
                company_id=company_id,
                period_ref=period_ref,
                insight_type=insight_type,
                status=status,
                details_json=json.dumps(details),
                orchestrator_run_id=orchestrator_run_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_insight_generated(self, *, payload: dict[str, object]) -> str:
        event = IntegrationEvent(topic="insight.generated.v1", payload=payload)
        self.session.add(
            InsightPublishedEventModel(
                event_id=event.event_id,
                company_id=str(payload["company_id"]),
                period_ref=str(payload["period_ref"]),
                insight_type=str(payload["insight_type"]),
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id
