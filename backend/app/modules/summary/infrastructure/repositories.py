from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.models import ImportJobModel
from app.modules.pipeline.infrastructure.models import PipelineRunModel
from app.modules.rule.infrastructure.models import RuleResultModel
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

        latest_import = self._safe_scalar_one_or_none(
            select(ImportJobModel)
            .where(ImportJobModel.company_id == company_id)
            .order_by(ImportJobModel.finished_at.desc().nullslast(), ImportJobModel.started_at.desc())
            .limit(1)
        )

        latest_pipeline = self._safe_scalar_one_or_none(
            select(PipelineRunModel)
            .where(PipelineRunModel.company_id == company_id)
            .order_by(PipelineRunModel.finished_at.desc().nullslast(), PipelineRunModel.started_at.desc())
            .limit(1)
        )

        pipeline_duration_ms = None
        if latest_pipeline is not None and latest_pipeline.started_at and latest_pipeline.finished_at:
            pipeline_duration_ms = int((latest_pipeline.finished_at - latest_pipeline.started_at).total_seconds() * 1000)

        data_quality = "excellent"
        if latest_import is not None and latest_import.total_rows > 0:
            failed_ratio = latest_import.failed_rows / latest_import.total_rows
            if failed_ratio >= 0.15:
                data_quality = "critical"
            elif failed_ratio >= 0.07:
                data_quality = "attention"
            elif failed_ratio >= 0.02:
                data_quality = "good"

        return SummarySourcePayload(
            company_id=company_id,
            period_ref=effective_period,
            generated_at=score.calculated_at,
            scores={
                "overall": score.overall_score,
                "financial": score.financial_score,
                "commercial": score.commercial_score,
                "operational": score.operational_score,
                "inventory": float(score.inventory_score or 0.0),
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
                    "alert_id": item.rule_result_id,
                    "rule_id": item.rule_id,
                    "kpi_id": item.kpi_id,
                    "metric_value": item.metric_value,
                    "severity": item.severity,
                    "priority": item.priority,
                    "title": item.alert_title,
                    "description": item.alert_description,
                }
                for item in self.session.execute(
                    select(RuleResultModel)
                    .where(
                        RuleResultModel.company_id == company_id,
                        RuleResultModel.period_ref == effective_period,
                    )
                    .order_by(RuleResultModel.fired_at.desc())
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
            dashboard={
                "last_import": latest_import.finished_at.isoformat() if latest_import and latest_import.finished_at else None,
                "last_pipeline": latest_pipeline.status.lower() if latest_pipeline else "unknown",
                "pipeline_duration_ms": pipeline_duration_ms,
                "summary_version": "3.1",
                "refresh_interval_seconds": 300,
                "data_quality": data_quality,
            },
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

    def _safe_scalar_one_or_none(self, statement: Select[Any]) -> Any | None:
        try:
            return self.session.execute(statement).scalar_one_or_none()
        except OperationalError as exc:
            message = str(exc).lower()
            if "no such table" in message or "does not exist" in message:
                return None
            raise
