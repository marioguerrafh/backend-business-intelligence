from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.rule.domain.entities import KPIValue, RuleExecutionResult
from app.modules.rule.infrastructure.models import RuleAuditLogModel, RulePublishedEventModel, RuleResultModel
from app.modules.summary.infrastructure.models import KPIResultModel
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class SqlAlchemyRuleRepository:
    session: Session

    def load_kpis_for_period(self, *, company_id: str, period_ref: str) -> list[KPIValue]:
        rows = self.session.execute(
            select(KPIResultModel).where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.period_ref == period_ref,
            )
        ).scalars().all()
        return [KPIValue(kpi_id=row.kpi_id, value=float(row.value)) for row in rows]

    def load_kpi_history(self, *, company_id: str, kpi_id: str, upto_period_ref: str, limit: int = 36) -> list[float]:
        rows = self.session.execute(
            select(KPIResultModel)
            .where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.kpi_id == kpi_id,
                KPIResultModel.period_ref <= upto_period_ref,
            )
            .order_by(KPIResultModel.period_ref.asc())
            .limit(limit)
        ).scalars().all()
        return [float(row.value) for row in rows]

    def has_rule_result(self, *, company_id: str, period_ref: str, kpi_id: str, rule_id: str) -> bool:
        model = self.session.execute(
            select(RuleResultModel).where(
                RuleResultModel.company_id == company_id,
                RuleResultModel.period_ref == period_ref,
                RuleResultModel.kpi_id == kpi_id,
                RuleResultModel.rule_id == rule_id,
            )
        ).scalar_one_or_none()
        return model is not None

    def save_rule_result(self, result: RuleExecutionResult) -> str:
        model = self.session.execute(
            select(RuleResultModel).where(
                RuleResultModel.company_id == result.company_id,
                RuleResultModel.period_ref == result.period_ref,
                RuleResultModel.kpi_id == result.kpi_id,
                RuleResultModel.rule_id == result.rule_id,
            )
        ).scalar_one_or_none()

        if model is None:
            model = RuleResultModel(
                rule_result_id=result.alert_id,
                company_id=result.company_id,
                period_ref=result.period_ref,
                kpi_id=result.kpi_id,
                rule_id=result.rule_id,
                severity=result.severity,
                priority=result.priority,
                alert_title=result.title,
                alert_description=result.description,
                metric_value=result.metric_value,
                fired_at=result.fired_at,
                orchestrator_run_id=result.orchestrator_run_id,
            )
            self.session.add(model)
        else:
            model.severity = result.severity
            model.priority = result.priority
            model.alert_title = result.title
            model.alert_description = result.description
            model.metric_value = result.metric_value
            model.fired_at = result.fired_at
            model.orchestrator_run_id = result.orchestrator_run_id
        self.session.flush()
        return model.rule_result_id

    def add_audit(
        self,
        *,
        company_id: str,
        period_ref: str,
        kpi_id: str,
        rule_id: str,
        status: str,
        expression: str,
        trace: list[str],
        fired: bool,
        orchestrator_run_id: str,
        error_message: str | None,
    ) -> None:
        self.session.add(
            RuleAuditLogModel(
                audit_log_id=f"raud_{uuid4().hex[:16]}",
                company_id=company_id,
                period_ref=period_ref,
                kpi_id=kpi_id,
                rule_id=rule_id,
                status=status,
                expression=expression,
                trace_json=json.dumps(trace),
                fired="true" if fired else "false",
                error_message=error_message,
                orchestrator_run_id=orchestrator_run_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_rule_executed(self, *, payload: dict[str, object]) -> str:
        event = IntegrationEvent(topic="rule.executed.v1", payload=payload)
        self.session.add(
            RulePublishedEventModel(
                event_id=event.event_id,
                company_id=str(payload["company_id"]),
                period_ref=str(payload["period_ref"]),
                rule_id=str(payload["rule_id"]),
                kpi_id=str(payload["kpi_id"]),
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id
