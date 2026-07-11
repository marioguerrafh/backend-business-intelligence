from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.models import ImportedFinancialFactModel, ImportedSaleFactModel, ImportJobModel
from app.modules.kpi.application.orchestrator_use_case import ExistingRun
from app.modules.kpi.infrastructure.models import KPIPublishedEventModel, KPIOrchestratorAuditLogModel, OrchestratorRunModel
from app.modules.summary.infrastructure.models import KPIResultModel
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class KPIOrchestratorRepository:
    session: Session

    def existing_run(self, *, company_id: str, period_ref: str, orchestrator_run_id: str) -> ExistingRun | None:
        model = self.session.execute(
            select(OrchestratorRunModel).where(
                OrchestratorRunModel.company_id == company_id,
                OrchestratorRunModel.period_ref == period_ref,
                OrchestratorRunModel.orchestrator_run_id == orchestrator_run_id,
                OrchestratorRunModel.pipeline_stage == "kpi",
            )
        ).scalar_one_or_none()
        if model is None:
            return None
        return ExistingRun(orchestrator_run_id=model.orchestrator_run_id, status=model.status)

    def start_run(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        correlation_id: str | None,
    ) -> None:
        self.session.add(
            OrchestratorRunModel(
                orchestrator_run_pk=f"run_{uuid4().hex[:16]}",
                orchestrator_run_id=orchestrator_run_id,
                company_id=company_id,
                period_ref=period_ref,
                pipeline_stage="kpi",
                started_at=datetime.now(timezone.utc),
                finished_at=None,
                status="running",
                error_summary=None,
                correlation_id=correlation_id,
            )
        )
        self.session.flush()

    def finish_run(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        status: str,
        error_summary: str | None,
    ) -> None:
        model = self.session.execute(
            select(OrchestratorRunModel).where(
                OrchestratorRunModel.company_id == company_id,
                OrchestratorRunModel.period_ref == period_ref,
                OrchestratorRunModel.orchestrator_run_id == orchestrator_run_id,
                OrchestratorRunModel.pipeline_stage == "kpi",
            )
        ).scalar_one()
        model.status = status
        model.error_summary = error_summary
        model.finished_at = datetime.now(timezone.utc)
        self.session.flush()

    def resolve_period_metrics(self, *, company_id: str, import_job_id: str, template: str) -> dict[str, dict[str, float]]:
        if template == "sales":
            return self._sales_period_metrics(company_id=company_id, import_job_id=import_job_id)
        if template == "financial":
            return self._financial_period_metrics(company_id=company_id, import_job_id=import_job_id)
        return {}

    def resolve_import_job_period(self, *, company_id: str, import_job_id: str) -> str:
        model = self.session.execute(
            select(ImportJobModel).where(
                ImportJobModel.import_job_id == import_job_id,
                ImportJobModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if model is None:
            raise ValueError("import job not found")

        pivot = model.finished_at or model.started_at
        return pivot.strftime("%Y-%m")

    def upsert_kpi_result(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        formula_id: str,
        kpi_id: str,
        kpi_name: str,
        value: float,
        unit: str,
        confidence_score: float,
        calculated_at: datetime,
    ) -> None:
        model = self.session.execute(
            select(KPIResultModel).where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.period_ref == period_ref,
                KPIResultModel.kpi_id == kpi_id,
            )
        ).scalar_one_or_none()
        if model is None:
            model = KPIResultModel(
                kpi_result_id=f"kpi_{uuid4().hex[:16]}",
                company_id=company_id,
                period_ref=period_ref,
                period_grain="month",
                kpi_id=kpi_id,
                formula_id=formula_id,
                kpi_name=kpi_name,
                value=value,
                unit=unit,
                confidence_score=confidence_score,
                trend=None,
                health=None,
                orchestrator_run_id=orchestrator_run_id,
                calculated_at=calculated_at,
            )
            self.session.add(model)
        else:
            model.period_grain = "month"
            model.formula_id = formula_id
            model.kpi_name = kpi_name
            model.value = value
            model.unit = unit
            model.confidence_score = confidence_score
            model.orchestrator_run_id = orchestrator_run_id
            model.calculated_at = calculated_at
        self.session.flush()

    def add_audit_entry(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        formula_id: str,
        kpi_id: str,
        status: str,
        execution_steps: list[str],
        inputs_used: dict[str, object],
        result_value: float | None,
        error_message: str | None,
    ) -> None:
        self.session.add(
            KPIOrchestratorAuditLogModel(
                audit_log_id=f"kaud_{uuid4().hex[:16]}",
                orchestrator_run_id=orchestrator_run_id,
                company_id=company_id,
                period_ref=period_ref,
                formula_id=formula_id,
                kpi_id=kpi_id,
                status=status,
                execution_steps_json=json.dumps(execution_steps),
                inputs_used_json=json.dumps(inputs_used),
                result_value=str(result_value) if result_value is not None else None,
                error_message=error_message,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_kpi_recalculated(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        kpi_id: str,
        formula_id: str,
        value: float,
        unit: str,
        confidence_score: float,
    ) -> str:
        event = IntegrationEvent(
            topic="kpi.recalculated.v1",
            payload={
                "company_id": company_id,
                "period_ref": period_ref,
                "kpi_id": kpi_id,
                "formula_id": formula_id,
                "value": value,
                "unit": unit,
                "confidence_score": confidence_score,
                "orchestrator_run_id": orchestrator_run_id,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.session.add(
            KPIPublishedEventModel(
                event_id=event.event_id,
                orchestrator_run_id=orchestrator_run_id,
                company_id=company_id,
                period_ref=period_ref,
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id

    def _sales_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedSaleFactModel).where(
                ImportedSaleFactModel.company_id == company_id,
                ImportedSaleFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.transaction_date.strftime("%Y-%m")
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_sales.gross_revenue": 0.0,
                    "fact_sales.tax_amount": 0.0,
                    "fact_sales.discount_amount": 0.0,
                    "fact_sales.return_amount": 0.0,
                    "fact_sales.net_revenue": 0.0,
                    "fact_sales.quantity_sold": 0.0,
                    "fact_sales.cogs_amount": 0.0,
                },
            )
            agg["fact_sales.gross_revenue"] += float(row.gross_revenue)
            agg["fact_sales.tax_amount"] += float(row.tax_amount)
            agg["fact_sales.discount_amount"] += float(row.discount_amount)
            agg["fact_sales.return_amount"] += float(row.return_amount)
            agg["fact_sales.net_revenue"] += float(row.net_revenue)
            agg["fact_sales.quantity_sold"] += float(row.quantity_sold)
            agg["fact_sales.cogs_amount"] += float(row.cogs_amount)
        return by_period

    def _financial_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedFinancialFactModel).where(
                ImportedFinancialFactModel.company_id == company_id,
                ImportedFinancialFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.transaction_date.strftime("%Y-%m")
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_finance_cashflow.cash_in_amount": 0.0,
                    "fact_finance_cashflow.cash_out_amount": 0.0,
                    "fact_finance_cashflow.operating_cash_flow_amount": 0.0,
                },
            )
            agg["fact_finance_cashflow.cash_in_amount"] += float(row.cash_in_amount)
            agg["fact_finance_cashflow.cash_out_amount"] += float(row.cash_out_amount)
            agg["fact_finance_cashflow.operating_cash_flow_amount"] += float(row.operating_cash_flow_amount)
        return by_period
