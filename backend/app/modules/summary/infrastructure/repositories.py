from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.modules.summary.application.ports.repository import (
    SummaryProjectionRecord,
    SummaryRepository,
    SummarySourcePayload,
)
from app.modules.summary.domain.entities import SummaryAggregate
from app.modules.summary.infrastructure.models import (
    ExecutiveScoreModel,
    InsightResultModel,
    KPIResultModel,
    RecommendationResultModel,
    RuleEvaluationModel,
    SummaryAuditLogModel,
    SummaryProjectionModel,
    TimelineSnapshotModel,
)


class SqlAlchemySummaryRepository(SummaryRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_projection(self, *, company_id: str, period_ref: str | None) -> SummaryProjectionRecord | None:
        query: Select[tuple[SummaryProjectionModel]] = select(SummaryProjectionModel).where(
            SummaryProjectionModel.company_id == company_id,
        )
        if period_ref:
            query = query.where(SummaryProjectionModel.period_ref == period_ref)
        projection = self.session.execute(
            query.order_by(SummaryProjectionModel.generated_at.desc()).limit(1)
        ).scalar_one_or_none()

        if projection is None:
            return None
        return SummaryProjectionRecord(
            summary_id=projection.summary_id,
            company_id=projection.company_id,
            period_ref=projection.period_ref,
            payload=dict(projection.payload_json),
            generated_at=projection.generated_at,
        )

    def load_source_payload(self, *, company_id: str, period_ref: str | None) -> SummarySourcePayload | None:
        score = self._latest_score(company_id=company_id, period_ref=period_ref)
        if score is None:
            return None

        effective_period = score.period_ref
        timeline_rows = self.session.execute(
            select(TimelineSnapshotModel)
            .where(TimelineSnapshotModel.company_id == company_id)
            .order_by(TimelineSnapshotModel.snapshot_date.desc())
            .limit(30)
        ).scalars().all()

        return SummarySourcePayload(
            company_id=company_id,
            period_ref=effective_period,
            generated_at=score.calculated_at,
            scores={
                "overall": score.overall_score,
                "financial": score.financial_score,
                "commercial": score.commercial_score,
                "operational": score.operational_score,
            },
            kpis=tuple(
                {
                    "kpi_id": item.kpi_id,
                    "name": item.kpi_name,
                    "value": item.value,
                    "unit": item.unit,
                    "trend": item.trend,
                    "health": item.health,
                }
                for item in self.session.execute(
                    select(KPIResultModel)
                    .where(
                        KPIResultModel.company_id == company_id,
                        KPIResultModel.period_ref == effective_period,
                    )
                    .order_by(KPIResultModel.kpi_id.asc())
                    .limit(20)
                ).scalars()
            ),
            alerts=tuple(
                {
                    "alert_id": item.rule_evaluation_id,
                    "severity": item.severity,
                    "priority": item.priority,
                    "title": item.title,
                    "description": item.description,
                }
                for item in self.session.execute(
                    select(RuleEvaluationModel)
                    .where(
                        RuleEvaluationModel.company_id == company_id,
                        RuleEvaluationModel.period_ref == effective_period,
                    )
                    .order_by(RuleEvaluationModel.fired_at.desc())
                    .limit(10)
                ).scalars()
            ),
            insights=tuple(
                {
                    "insight_id": item.insight_result_id,
                    "type": item.insight_type,
                    "statement": item.statement,
                    "evidence": item.evidence_json,
                }
                for item in self.session.execute(
                    select(InsightResultModel)
                    .where(
                        InsightResultModel.company_id == company_id,
                        InsightResultModel.period_ref == effective_period,
                    )
                    .order_by(InsightResultModel.generated_at.desc())
                    .limit(10)
                ).scalars()
            ),
            recommendations=tuple(
                {
                    "recommendation_id": item.recommendation_id,
                    "title": item.title,
                    "rank": item.rank_score,
                    "expected_impact": item.expected_impact_json,
                    "owner_role": item.owner_role,
                    "sla_target": item.sla_target,
                }
                for item in self.session.execute(
                    select(RecommendationResultModel)
                    .where(
                        RecommendationResultModel.company_id == company_id,
                        RecommendationResultModel.period_ref == effective_period,
                    )
                    .order_by(RecommendationResultModel.rank_score.desc())
                    .limit(10)
                ).scalars()
            ),
            timeline_points=tuple(
                {
                    "snapshot_date": item.snapshot_date.isoformat(),
                    "overall_score": item.overall_score,
                    "financial_score": item.financial_score,
                    "commercial_score": item.commercial_score,
                    "operational_score": item.operational_score,
                }
                for item in timeline_rows
            ),
            next_risks=tuple(timeline_rows[0].top_risks_json if timeline_rows else []),
        )

    def save_projection(self, aggregate: SummaryAggregate) -> None:
        model = SummaryProjectionModel(
            summary_id=aggregate.summary_id,
            company_id=aggregate.company_id,
            period_ref=aggregate.period_ref,
            payload_json=aggregate.to_payload(),
            generated_at=aggregate.generated_at,
        )
        self.session.add(model)
        self.session.flush()

    def audit_access(
        self,
        *,
        company_id: str,
        period_ref: str,
        summary_id: str,
        correlation_id: str | None,
        cache_hit: bool,
        duration_ms: int,
    ) -> None:
        self.session.add(
            SummaryAuditLogModel(
                audit_log_id=f"aud_{uuid4().hex[:16]}",
                company_id=company_id,
                period_ref=period_ref,
                summary_id=summary_id,
                correlation_id=correlation_id,
                cache_hit=cache_hit,
                duration_ms=duration_ms,
                requested_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def _latest_score(self, *, company_id: str, period_ref: str | None) -> ExecutiveScoreModel | None:
        query: Select[tuple[ExecutiveScoreModel]] = select(ExecutiveScoreModel).where(
            ExecutiveScoreModel.company_id == company_id,
        )
        if period_ref:
            query = query.where(ExecutiveScoreModel.period_ref == period_ref)
        return self.session.execute(query.order_by(ExecutiveScoreModel.calculated_at.desc()).limit(1)).scalar_one_or_none()
