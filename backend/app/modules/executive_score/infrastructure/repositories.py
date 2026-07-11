from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.executive_score.domain.entities import ExecutiveScoreAggregate
from app.modules.executive_score.infrastructure.models import ExecutiveScoreAuditLogModel, ExecutiveScorePublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import ExecutiveScoreModel, KPIResultModel, RecommendationResultModel, TimelineSnapshotModel
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class SqlAlchemyExecutiveScoreRepository:
    session: Session

    def load_kpis_for_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(KPIResultModel).where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.period_ref == period_ref,
            )
        ).scalars().all()
        return {row.kpi_id: float(row.value) for row in rows}

    def compute_rule_penalty(self, *, company_id: str, period_ref: str) -> float:
        rows = self.session.execute(
            select(RuleResultModel.severity).where(
                RuleResultModel.company_id == company_id,
                RuleResultModel.period_ref == period_ref,
            )
        ).all()
        penalty = 0.0
        for row in rows:
            severity = str(row[0]).upper()
            if severity == "CRITICAL":
                penalty += 12.0
            elif severity == "HIGH":
                penalty += 8.0
            elif severity == "MEDIUM":
                penalty += 4.0
            elif severity == "LOW":
                penalty += 2.0
        return penalty

    def compute_recommendation_bonus(self, *, company_id: str, period_ref: str) -> float:
        avg_rank = self.session.execute(
            select(func.avg(RecommendationResultModel.rank_score)).where(
                RecommendationResultModel.company_id == company_id,
                RecommendationResultModel.period_ref == period_ref,
            )
        ).scalar_one_or_none()
        if avg_rank is None:
            return 0.0
        return min(5.0, float(avg_rank) * 5.0)

    def save_executive_score(self, aggregate: ExecutiveScoreAggregate) -> None:
        model = self.session.execute(
            select(ExecutiveScoreModel).where(
                ExecutiveScoreModel.company_id == aggregate.company_id,
                ExecutiveScoreModel.period_ref == aggregate.period_ref,
            )
        ).scalar_one_or_none()

        if model is None:
            model = ExecutiveScoreModel(
                executive_score_id=aggregate.executive_score_id,
                company_id=aggregate.company_id,
                period_ref=aggregate.period_ref,
                financial_score=aggregate.financial_score,
                commercial_score=aggregate.commercial_score,
                operational_score=aggregate.operational_score,
                inventory_score=aggregate.inventory_score,
                overall_score=aggregate.executive_score,
                score_version=aggregate.score_version,
                calculated_at=aggregate.calculated_at,
            )
            self.session.add(model)
        else:
            model.financial_score = aggregate.financial_score
            model.commercial_score = aggregate.commercial_score
            model.operational_score = aggregate.operational_score
            model.inventory_score = aggregate.inventory_score
            model.overall_score = aggregate.executive_score
            model.score_version = aggregate.score_version
            model.calculated_at = aggregate.calculated_at

        self.session.flush()

    def save_timeline_snapshot(
        self,
        *,
        company_id: str,
        period_ref: str,
        financial_score: float,
        commercial_score: float,
        operational_score: float,
        executive_score: float,
    ) -> None:
        snapshot_date = self._period_to_date(period_ref)
        model = self.session.execute(
            select(TimelineSnapshotModel).where(
                TimelineSnapshotModel.company_id == company_id,
                TimelineSnapshotModel.snapshot_date == snapshot_date,
            )
        ).scalar_one_or_none()

        risks = [
            {
                "risk_code": row.rule_id,
                "severity": row.severity,
                "priority": row.priority,
            }
            for row in self.session.execute(
                select(RuleResultModel)
                .where(
                    RuleResultModel.company_id == company_id,
                    RuleResultModel.period_ref == period_ref,
                )
                .order_by(RuleResultModel.fired_at.desc())
                .limit(5)
            ).scalars().all()
        ]

        if model is None:
            model = TimelineSnapshotModel(
                timeline_snapshot_id=f"tls_{uuid4().hex[:16]}",
                company_id=company_id,
                snapshot_date=snapshot_date,
                overall_score=executive_score,
                financial_score=financial_score,
                commercial_score=commercial_score,
                operational_score=operational_score,
                top_risks_json=risks,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(model)
        else:
            model.overall_score = executive_score
            model.financial_score = financial_score
            model.commercial_score = commercial_score
            model.operational_score = operational_score
            model.top_risks_json = risks

        self.session.flush()

    def add_audit(
        self,
        *,
        company_id: str,
        period_ref: str,
        status: str,
        details: dict[str, object],
        orchestrator_run_id: str,
    ) -> None:
        self.session.add(
            ExecutiveScoreAuditLogModel(
                audit_log_id=f"esad_{uuid4().hex[:16]}",
                company_id=company_id,
                period_ref=period_ref,
                status=status,
                details_json=json.dumps(details),
                orchestrator_run_id=orchestrator_run_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_executive_score_updated(self, *, payload: dict[str, object]) -> str:
        event = IntegrationEvent(topic="executive.score.updated.v1", payload=payload)
        self.session.add(
            ExecutiveScorePublishedEventModel(
                event_id=event.event_id,
                company_id=str(payload["company_id"]),
                period_ref=str(payload["period_ref"]),
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id

    def _period_to_date(self, period_ref: str) -> date:
        if len(period_ref) >= 10 and period_ref[4] == "-" and period_ref[7] == "-":
            return datetime.strptime(period_ref[:10], "%Y-%m-%d").date()
        if len(period_ref) >= 7 and period_ref[4] == "-":
            return datetime.strptime(f"{period_ref[:7]}-01", "%Y-%m-%d").date()
        return datetime.now(timezone.utc).date()
