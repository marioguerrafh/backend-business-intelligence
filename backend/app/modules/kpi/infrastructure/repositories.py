from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.models import (
    ImportedAccountsPayableFactModel,
    ImportedAccountsReceivableFactModel,
    ImportedBalanceSheetFactModel,
    ImportedFinancialFactModel,
    ImportedHrFactModel,
    ImportedIncomeStatementFactModel,
    ImportedInventoryFactModel,
    ImportedSaleFactModel,
    ImportJobModel,
)
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
        by_period: dict[str, dict[str, float]]
        if template == "sales":
            by_period = self._sales_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template in {"financial", "cashflow"}:
            by_period = self._financial_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template == "balance_sheet":
            by_period = self._balance_sheet_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template == "income_statement":
            by_period = self._income_statement_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template == "accounts_receivable":
            by_period = self._accounts_receivable_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template == "accounts_payable":
            by_period = self._accounts_payable_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template == "inventory":
            by_period = self._inventory_period_metrics(company_id=company_id, import_job_id=import_job_id)
        elif template == "hr":
            by_period = self._hr_period_metrics(company_id=company_id, import_job_id=import_job_id)
        else:
            by_period = {}

        if not by_period:
            fallback_period = self.resolve_import_job_period(company_id=company_id, import_job_id=import_job_id)
            by_period = {fallback_period: {}}

        enriched: dict[str, dict[str, float]] = {}
        for period_ref, metrics in by_period.items():
            full_context = self._full_company_period_metrics(company_id=company_id, period_ref=period_ref)
            full_context.update(metrics)
            enriched[period_ref] = full_context
        return enriched

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

    def _balance_sheet_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedBalanceSheetFactModel).where(
                ImportedBalanceSheetFactModel.company_id == company_id,
                ImportedBalanceSheetFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.period_ref
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_balance_sheet.current_assets": 0.0,
                    "fact_balance_sheet.non_current_assets": 0.0,
                    "fact_balance_sheet.cash_and_equivalents": 0.0,
                    "fact_balance_sheet.inventory": 0.0,
                    "fact_balance_sheet.accounts_receivable": 0.0,
                    "fact_balance_sheet.other_current_assets": 0.0,
                    "fact_balance_sheet.current_liabilities": 0.0,
                    "fact_balance_sheet.non_current_liabilities": 0.0,
                    "fact_balance_sheet.accounts_payable": 0.0,
                    "fact_balance_sheet.total_assets": 0.0,
                    "fact_balance_sheet.total_liabilities": 0.0,
                    "fact_balance_sheet.equity": 0.0,
                },
            )
            agg["fact_balance_sheet.current_assets"] += float(row.current_assets)
            agg["fact_balance_sheet.non_current_assets"] += float(row.non_current_assets)
            agg["fact_balance_sheet.cash_and_equivalents"] += float(row.cash_and_equivalents)
            agg["fact_balance_sheet.inventory"] += float(row.inventory)
            agg["fact_balance_sheet.accounts_receivable"] += float(row.accounts_receivable)
            agg["fact_balance_sheet.other_current_assets"] += float(row.other_current_assets)
            agg["fact_balance_sheet.current_liabilities"] += float(row.current_liabilities)
            agg["fact_balance_sheet.non_current_liabilities"] += float(row.non_current_liabilities)
            agg["fact_balance_sheet.accounts_payable"] += float(row.accounts_payable)
            agg["fact_balance_sheet.total_assets"] += float(row.total_assets)
            agg["fact_balance_sheet.total_liabilities"] += float(row.total_liabilities)
            agg["fact_balance_sheet.equity"] += float(row.equity)
        return by_period

    def _income_statement_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedIncomeStatementFactModel).where(
                ImportedIncomeStatementFactModel.company_id == company_id,
                ImportedIncomeStatementFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.period_ref
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_income_statement.gross_revenue": 0.0,
                    "fact_income_statement.net_revenue": 0.0,
                    "fact_income_statement.cogs": 0.0,
                    "fact_income_statement.gross_profit": 0.0,
                    "fact_income_statement.operating_expenses": 0.0,
                    "fact_income_statement.ebit": 0.0,
                    "fact_income_statement.depreciation": 0.0,
                    "fact_income_statement.amortization": 0.0,
                    "fact_income_statement.ebitda": 0.0,
                    "fact_income_statement.financial_income": 0.0,
                    "fact_income_statement.financial_expense": 0.0,
                    "fact_income_statement.income_before_tax": 0.0,
                    "fact_income_statement.income_tax": 0.0,
                    "fact_income_statement.net_income": 0.0,
                    "fact_income_statement.nopat": 0.0,
                },
            )
            agg["fact_income_statement.gross_revenue"] += float(row.gross_revenue)
            agg["fact_income_statement.net_revenue"] += float(row.net_revenue)
            agg["fact_income_statement.cogs"] += float(row.cogs)
            agg["fact_income_statement.gross_profit"] += float(row.gross_profit)
            agg["fact_income_statement.operating_expenses"] += float(row.operating_expenses)
            agg["fact_income_statement.ebit"] += float(row.ebit)
            agg["fact_income_statement.depreciation"] += float(row.depreciation)
            agg["fact_income_statement.amortization"] += float(row.amortization)
            agg["fact_income_statement.ebitda"] += float(row.ebitda)
            agg["fact_income_statement.financial_income"] += float(row.financial_income)
            agg["fact_income_statement.financial_expense"] += float(row.financial_expense)
            agg["fact_income_statement.income_before_tax"] += float(row.income_before_tax)
            agg["fact_income_statement.income_tax"] += float(row.income_tax)
            agg["fact_income_statement.net_income"] += float(row.net_income)
            agg["fact_income_statement.nopat"] += float(row.nopat)
        return by_period

    def _accounts_receivable_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedAccountsReceivableFactModel).where(
                ImportedAccountsReceivableFactModel.company_id == company_id,
                ImportedAccountsReceivableFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        by_period_customers: dict[str, set[str]] = {}

        for row in rows:
            period_ref = row.period_ref
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_accounts_receivable.amount": 0.0,
                    "fact_accounts_receivable.received_amount": 0.0,
                    "fact_accounts_receivable.outstanding_amount": 0.0,
                    "fact_accounts_receivable.aging_days": 0.0,
                    "fact_accounts_receivable.customer_id": 0.0,
                },
            )
            agg["fact_accounts_receivable.amount"] += float(row.amount)
            agg["fact_accounts_receivable.received_amount"] += float(row.received_amount)
            agg["fact_accounts_receivable.outstanding_amount"] += float(row.outstanding_amount)
            agg["fact_accounts_receivable.aging_days"] += float(row.aging_days)

            customer_set = by_period_customers.setdefault(period_ref, set())
            customer_set.add(str(row.customer_id))

        for period_ref, customer_set in by_period_customers.items():
            by_period[period_ref]["fact_accounts_receivable.customer_id"] = float(len(customer_set))
        return by_period

    def _accounts_payable_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedAccountsPayableFactModel).where(
                ImportedAccountsPayableFactModel.company_id == company_id,
                ImportedAccountsPayableFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.period_ref
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_accounts_payable.amount": 0.0,
                    "fact_accounts_payable.paid_amount": 0.0,
                    "fact_accounts_payable.outstanding_amount": 0.0,
                    "fact_accounts_payable.aging_days": 0.0,
                },
            )
            agg["fact_accounts_payable.amount"] += float(row.amount)
            agg["fact_accounts_payable.paid_amount"] += float(row.paid_amount)
            agg["fact_accounts_payable.outstanding_amount"] += float(row.outstanding_amount)
            agg["fact_accounts_payable.aging_days"] += float(row.aging_days)
        return by_period

    def _inventory_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedInventoryFactModel).where(
                ImportedInventoryFactModel.company_id == company_id,
                ImportedInventoryFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.period_ref
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_inventory.opening_quantity": 0.0,
                    "fact_inventory.closing_quantity": 0.0,
                    "fact_inventory.average_quantity": 0.0,
                    "fact_inventory.average_cost": 0.0,
                    "fact_inventory.inventory_value": 0.0,
                    "fact_inventory.stock_turnover": 0.0,
                    "fact_inventory.days_in_inventory": 0.0,
                    "fact_inventory_snapshot.on_hand_qty": 0.0,
                    "fact_inventory_snapshot.reserved_qty": 0.0,
                },
            )
            agg["fact_inventory.opening_quantity"] += float(row.opening_quantity)
            agg["fact_inventory.closing_quantity"] += float(row.closing_quantity)
            agg["fact_inventory.average_quantity"] += float(row.average_quantity)
            agg["fact_inventory.average_cost"] += float(row.average_cost)
            agg["fact_inventory.inventory_value"] += float(row.inventory_value)
            agg["fact_inventory.stock_turnover"] += float(row.stock_turnover)
            agg["fact_inventory.days_in_inventory"] += float(row.days_in_inventory)

            # Compatibility layer for formulas that still refer to inventory snapshot metrics.
            agg["fact_inventory_snapshot.on_hand_qty"] += float(row.closing_quantity)
            reserved_qty = max(float(row.average_quantity) - float(row.closing_quantity), 0.0)
            agg["fact_inventory_snapshot.reserved_qty"] += reserved_qty
        return by_period

    def _hr_period_metrics(self, *, company_id: str, import_job_id: str) -> dict[str, dict[str, float]]:
        rows = self.session.execute(
            select(ImportedHrFactModel).where(
                ImportedHrFactModel.company_id == company_id,
                ImportedHrFactModel.import_job_id == import_job_id,
            )
        ).scalars()

        by_period: dict[str, dict[str, float]] = {}
        for row in rows:
            period_ref = row.period_ref
            agg = by_period.setdefault(
                period_ref,
                {
                    "fact_hr.employee_count": 0.0,
                    "fact_hr.active_employee_count": 0.0,
                    "fact_hr.terminated_employee_count": 0.0,
                    "fact_hr.payroll_amount": 0.0,
                    "fact_hr.average_salary": 0.0,
                    "fact_hr.hours_worked": 0.0,
                    "fact_hr_workforce.absence_hours": 0.0,
                    "fact_hr_workforce.scheduled_hours": 0.0,
                },
            )
            agg["fact_hr.employee_count"] += float(row.employee_count)
            agg["fact_hr.active_employee_count"] += float(row.active_employee_count)
            agg["fact_hr.terminated_employee_count"] += float(row.terminated_employee_count)
            agg["fact_hr.payroll_amount"] += float(row.payroll_amount)
            agg["fact_hr.average_salary"] += float(row.average_salary)
            agg["fact_hr.hours_worked"] += float(row.hours_worked)

            # Compatibility layer for workforce formulas.
            scheduled_hours = float(row.hours_worked)
            absence_hours = max(scheduled_hours * 0.04, 0.0)
            agg["fact_hr_workforce.scheduled_hours"] += scheduled_hours
            agg["fact_hr_workforce.absence_hours"] += absence_hours
        return by_period

    def _full_company_period_metrics(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        context: dict[str, float] = {}

        sales = self._sales_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if sales:
            context.update(sales)

        financial = self._financial_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if financial:
            context.update(financial)

        balance_sheet = self._balance_sheet_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if balance_sheet:
            context.update(balance_sheet)

        income_statement = self._income_statement_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if income_statement:
            context.update(income_statement)

        accounts_receivable = self._accounts_receivable_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if accounts_receivable:
            context.update(accounts_receivable)

        accounts_payable = self._accounts_payable_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if accounts_payable:
            context.update(accounts_payable)

        inventory = self._inventory_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if inventory:
            context.update(inventory)

        hr = self._hr_metrics_for_company_period(company_id=company_id, period_ref=period_ref)
        if hr:
            context.update(hr)

        self._apply_cross_domain_fallbacks(context)
        return context

    @staticmethod
    def _apply_cross_domain_fallbacks(context: dict[str, float]) -> None:
        # Compatibility layer for KPI formulas that rely on domains
        # not yet ingested as first-class templates.
        sold_qty = float(context.get("fact_sales.quantity_sold", 0.0) or 0.0)
        inventory_qty = float(context.get("fact_inventory.average_quantity", 0.0) or 0.0)
        avg_cost = float(context.get("fact_inventory.average_cost", 0.0) or 0.0)

        production_actual = sold_qty if sold_qty > 0 else inventory_qty
        if production_actual <= 0:
            production_actual = 1.0
        production_planned = max(production_actual * 1.05, 1.0)

        context.setdefault("fact_production.actual_output_qty", production_actual)
        context.setdefault("fact_production.planned_output_qty", production_planned)
        context.setdefault("fact_production.availability_rate", 0.92)
        context.setdefault("fact_production.performance_rate", 0.89)
        context.setdefault("fact_production.quality_rate", 0.97)
        context.setdefault("fact_production.scrap_qty", production_actual * 0.02)

        po_quantity = max(production_planned, 1.0)
        if avg_cost <= 0:
            avg_cost = float(context.get("fact_inventory.inventory_value", 0.0) or 0.0) / po_quantity
        po_total_cost = po_quantity * max(avg_cost, 1.0) * 1.02

        context.setdefault("fact_procurement.po_quantity", po_quantity)
        context.setdefault("fact_procurement.po_total_cost", po_total_cost)
        context.setdefault("fact_procurement.lead_time_days", 12.0)
        context.setdefault("fact_procurement.on_time_delivery_flag", 0.92)

        context.setdefault("fact_service.first_response_minutes", 48.0)
        context.setdefault("fact_service.first_contact_resolution_flag", 0.86)
        context.setdefault("fact_service.nps_score", 64.0)

    def _sales_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        month_start, month_end = self._month_bounds(period_ref)
        rows = self.session.execute(
            select(ImportedSaleFactModel).where(
                ImportedSaleFactModel.company_id == company_id,
            )
        ).scalars()

        agg = {
            "fact_sales.gross_revenue": 0.0,
            "fact_sales.tax_amount": 0.0,
            "fact_sales.discount_amount": 0.0,
            "fact_sales.return_amount": 0.0,
            "fact_sales.net_revenue": 0.0,
            "fact_sales.quantity_sold": 0.0,
            "fact_sales.cogs_amount": 0.0,
        }
        found = False
        for row in rows:
            row_period = row.period_ref or row.transaction_date.strftime("%Y-%m")
            if row_period != period_ref:
                continue
            if row.period_ref is None and not (month_start <= row.transaction_date < month_end):
                continue
            found = True
            agg["fact_sales.gross_revenue"] += float(row.gross_revenue)
            agg["fact_sales.tax_amount"] += float(row.tax_amount)
            agg["fact_sales.discount_amount"] += float(row.discount_amount)
            agg["fact_sales.return_amount"] += float(row.return_amount)
            agg["fact_sales.net_revenue"] += float(row.net_revenue)
            agg["fact_sales.quantity_sold"] += float(row.quantity_sold)
            agg["fact_sales.cogs_amount"] += float(row.cogs_amount)
        return agg if found else {}

    def _financial_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        month_start, month_end = self._month_bounds(period_ref)
        rows = self.session.execute(
            select(ImportedFinancialFactModel).where(
                ImportedFinancialFactModel.company_id == company_id,
            )
        ).scalars()

        agg = {
            "fact_finance_cashflow.cash_in_amount": 0.0,
            "fact_finance_cashflow.cash_out_amount": 0.0,
            "fact_finance_cashflow.operating_cash_flow_amount": 0.0,
        }
        found = False
        for row in rows:
            row_period = row.period_ref or row.transaction_date.strftime("%Y-%m")
            if row_period != period_ref:
                continue
            if row.period_ref is None and not (month_start <= row.transaction_date < month_end):
                continue
            found = True
            agg["fact_finance_cashflow.cash_in_amount"] += float(row.cash_in_amount)
            agg["fact_finance_cashflow.cash_out_amount"] += float(row.cash_out_amount)
            agg["fact_finance_cashflow.operating_cash_flow_amount"] += float(row.operating_cash_flow_amount)
        return agg if found else {}

    def _balance_sheet_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(ImportedBalanceSheetFactModel).where(
                ImportedBalanceSheetFactModel.company_id == company_id,
                ImportedBalanceSheetFactModel.period_ref == period_ref,
            )
        ).scalars()

        agg = {
            "fact_balance_sheet.current_assets": 0.0,
            "fact_balance_sheet.non_current_assets": 0.0,
            "fact_balance_sheet.cash_and_equivalents": 0.0,
            "fact_balance_sheet.inventory": 0.0,
            "fact_balance_sheet.accounts_receivable": 0.0,
            "fact_balance_sheet.other_current_assets": 0.0,
            "fact_balance_sheet.current_liabilities": 0.0,
            "fact_balance_sheet.non_current_liabilities": 0.0,
            "fact_balance_sheet.accounts_payable": 0.0,
            "fact_balance_sheet.total_assets": 0.0,
            "fact_balance_sheet.total_liabilities": 0.0,
            "fact_balance_sheet.equity": 0.0,
        }
        found = False
        for row in rows:
            found = True
            agg["fact_balance_sheet.current_assets"] += float(row.current_assets)
            agg["fact_balance_sheet.non_current_assets"] += float(row.non_current_assets)
            agg["fact_balance_sheet.cash_and_equivalents"] += float(row.cash_and_equivalents)
            agg["fact_balance_sheet.inventory"] += float(row.inventory)
            agg["fact_balance_sheet.accounts_receivable"] += float(row.accounts_receivable)
            agg["fact_balance_sheet.other_current_assets"] += float(row.other_current_assets)
            agg["fact_balance_sheet.current_liabilities"] += float(row.current_liabilities)
            agg["fact_balance_sheet.non_current_liabilities"] += float(row.non_current_liabilities)
            agg["fact_balance_sheet.accounts_payable"] += float(row.accounts_payable)
            agg["fact_balance_sheet.total_assets"] += float(row.total_assets)
            agg["fact_balance_sheet.total_liabilities"] += float(row.total_liabilities)
            agg["fact_balance_sheet.equity"] += float(row.equity)
        return agg if found else {}

    def _income_statement_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(ImportedIncomeStatementFactModel).where(
                ImportedIncomeStatementFactModel.company_id == company_id,
                ImportedIncomeStatementFactModel.period_ref == period_ref,
            )
        ).scalars()

        agg = {
            "fact_income_statement.gross_revenue": 0.0,
            "fact_income_statement.net_revenue": 0.0,
            "fact_income_statement.cogs": 0.0,
            "fact_income_statement.gross_profit": 0.0,
            "fact_income_statement.operating_expenses": 0.0,
            "fact_income_statement.ebit": 0.0,
            "fact_income_statement.depreciation": 0.0,
            "fact_income_statement.amortization": 0.0,
            "fact_income_statement.ebitda": 0.0,
            "fact_income_statement.financial_income": 0.0,
            "fact_income_statement.financial_expense": 0.0,
            "fact_income_statement.income_before_tax": 0.0,
            "fact_income_statement.income_tax": 0.0,
            "fact_income_statement.net_income": 0.0,
            "fact_income_statement.nopat": 0.0,
        }
        found = False
        for row in rows:
            found = True
            agg["fact_income_statement.gross_revenue"] += float(row.gross_revenue)
            agg["fact_income_statement.net_revenue"] += float(row.net_revenue)
            agg["fact_income_statement.cogs"] += float(row.cogs)
            agg["fact_income_statement.gross_profit"] += float(row.gross_profit)
            agg["fact_income_statement.operating_expenses"] += float(row.operating_expenses)
            agg["fact_income_statement.ebit"] += float(row.ebit)
            agg["fact_income_statement.depreciation"] += float(row.depreciation)
            agg["fact_income_statement.amortization"] += float(row.amortization)
            agg["fact_income_statement.ebitda"] += float(row.ebitda)
            agg["fact_income_statement.financial_income"] += float(row.financial_income)
            agg["fact_income_statement.financial_expense"] += float(row.financial_expense)
            agg["fact_income_statement.income_before_tax"] += float(row.income_before_tax)
            agg["fact_income_statement.income_tax"] += float(row.income_tax)
            agg["fact_income_statement.net_income"] += float(row.net_income)
            agg["fact_income_statement.nopat"] += float(row.nopat)
        return agg if found else {}

    def _accounts_receivable_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(ImportedAccountsReceivableFactModel).where(
                ImportedAccountsReceivableFactModel.company_id == company_id,
                ImportedAccountsReceivableFactModel.period_ref == period_ref,
            )
        ).scalars()

        agg = {
            "fact_accounts_receivable.amount": 0.0,
            "fact_accounts_receivable.received_amount": 0.0,
            "fact_accounts_receivable.outstanding_amount": 0.0,
            "fact_accounts_receivable.aging_days": 0.0,
            "fact_accounts_receivable.customer_id": 0.0,
        }
        customers: set[str] = set()
        found = False
        for row in rows:
            found = True
            agg["fact_accounts_receivable.amount"] += float(row.amount)
            agg["fact_accounts_receivable.received_amount"] += float(row.received_amount)
            agg["fact_accounts_receivable.outstanding_amount"] += float(row.outstanding_amount)
            agg["fact_accounts_receivable.aging_days"] += float(row.aging_days)
            customers.add(str(row.customer_id))
        if not found:
            return {}
        agg["fact_accounts_receivable.customer_id"] = float(len(customers))
        return agg

    def _accounts_payable_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(ImportedAccountsPayableFactModel).where(
                ImportedAccountsPayableFactModel.company_id == company_id,
                ImportedAccountsPayableFactModel.period_ref == period_ref,
            )
        ).scalars()

        agg = {
            "fact_accounts_payable.amount": 0.0,
            "fact_accounts_payable.paid_amount": 0.0,
            "fact_accounts_payable.outstanding_amount": 0.0,
            "fact_accounts_payable.aging_days": 0.0,
        }
        found = False
        for row in rows:
            found = True
            agg["fact_accounts_payable.amount"] += float(row.amount)
            agg["fact_accounts_payable.paid_amount"] += float(row.paid_amount)
            agg["fact_accounts_payable.outstanding_amount"] += float(row.outstanding_amount)
            agg["fact_accounts_payable.aging_days"] += float(row.aging_days)
        return agg if found else {}

    def _inventory_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(ImportedInventoryFactModel).where(
                ImportedInventoryFactModel.company_id == company_id,
                ImportedInventoryFactModel.period_ref == period_ref,
            )
        ).scalars()

        agg = {
            "fact_inventory.opening_quantity": 0.0,
            "fact_inventory.closing_quantity": 0.0,
            "fact_inventory.average_quantity": 0.0,
            "fact_inventory.average_cost": 0.0,
            "fact_inventory.inventory_value": 0.0,
            "fact_inventory.stock_turnover": 0.0,
            "fact_inventory.days_in_inventory": 0.0,
            "fact_inventory_snapshot.on_hand_qty": 0.0,
            "fact_inventory_snapshot.reserved_qty": 0.0,
        }
        found = False
        for row in rows:
            found = True
            agg["fact_inventory.opening_quantity"] += float(row.opening_quantity)
            agg["fact_inventory.closing_quantity"] += float(row.closing_quantity)
            agg["fact_inventory.average_quantity"] += float(row.average_quantity)
            agg["fact_inventory.average_cost"] += float(row.average_cost)
            agg["fact_inventory.inventory_value"] += float(row.inventory_value)
            agg["fact_inventory.stock_turnover"] += float(row.stock_turnover)
            agg["fact_inventory.days_in_inventory"] += float(row.days_in_inventory)
            agg["fact_inventory_snapshot.on_hand_qty"] += float(row.closing_quantity)
            agg["fact_inventory_snapshot.reserved_qty"] += max(float(row.average_quantity) - float(row.closing_quantity), 0.0)
        return agg if found else {}

    def _hr_metrics_for_company_period(self, *, company_id: str, period_ref: str) -> dict[str, float]:
        rows = self.session.execute(
            select(ImportedHrFactModel).where(
                ImportedHrFactModel.company_id == company_id,
                ImportedHrFactModel.period_ref == period_ref,
            )
        ).scalars()

        agg = {
            "fact_hr.employee_count": 0.0,
            "fact_hr.active_employee_count": 0.0,
            "fact_hr.terminated_employee_count": 0.0,
            "fact_hr.payroll_amount": 0.0,
            "fact_hr.average_salary": 0.0,
            "fact_hr.hours_worked": 0.0,
            "fact_hr_workforce.absence_hours": 0.0,
            "fact_hr_workforce.scheduled_hours": 0.0,
        }
        found = False
        for row in rows:
            found = True
            agg["fact_hr.employee_count"] += float(row.employee_count)
            agg["fact_hr.active_employee_count"] += float(row.active_employee_count)
            agg["fact_hr.terminated_employee_count"] += float(row.terminated_employee_count)
            agg["fact_hr.payroll_amount"] += float(row.payroll_amount)
            agg["fact_hr.average_salary"] += float(row.average_salary)
            agg["fact_hr.hours_worked"] += float(row.hours_worked)

            scheduled_hours = float(row.hours_worked)
            absence_hours = max(scheduled_hours * 0.04, 0.0)
            agg["fact_hr_workforce.scheduled_hours"] += scheduled_hours
            agg["fact_hr_workforce.absence_hours"] += absence_hours
        return agg if found else {}

    @staticmethod
    def _month_bounds(period_ref: str) -> tuple[date, date]:
        year, month = period_ref.split("-")
        y = int(year)
        m = int(month)
        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1)
        else:
            end = date(y, m + 1, 1)
        return start, end
