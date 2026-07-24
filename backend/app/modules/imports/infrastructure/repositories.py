from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import cast
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.modules.imports.application.contracts import ImportInconsistency
from app.modules.imports.infrastructure.models import (
    ImportInconsistencyModel,
    ImportJobModel,
    ImportPublishedEventModel,
)
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class ImportRepository:
    session: Session
    _table_columns_cache: dict[str, set[str]] = field(default_factory=dict, repr=False)

    def create_job(
        self,
        *,
        company_id: str,
        template: str,
        source_system: str,
        canonical_schema_version: str,
        correlation_id: str | None,
    ) -> str:
        job_id = f"imp_{uuid4().hex[:16]}"
        self.session.add(
            ImportJobModel(
                import_job_id=job_id,
                company_id=company_id,
                template=template,
                source_system=source_system,
                canonical_schema_version=canonical_schema_version,
                status="running",
                total_rows=0,
                imported_rows=0,
                failed_rows=0,
                correlation_id=correlation_id,
                started_at=datetime.now(timezone.utc),
                finished_at=None,
            )
        )
        self.session.flush()
        return job_id

    def finish_job(
        self,
        *,
        job_id: str,
        total_rows: int,
        imported_rows: int,
        failed_rows: int,
        status: str,
    ) -> None:
        model = self.session.get(ImportJobModel, job_id)
        if model is None:
            raise ValueError("import job not found")
        model.total_rows = total_rows
        model.imported_rows = imported_rows
        model.failed_rows = failed_rows
        model.status = status
        model.finished_at = datetime.now(timezone.utc)
        self.session.flush()

    def add_inconsistency(self, *, company_id: str, job_id: str, issue: ImportInconsistency) -> None:
        self.session.add(
            ImportInconsistencyModel(
                inconsistency_id=f"inc_{uuid4().hex[:16]}",
                import_job_id=job_id,
                company_id=company_id,
                row_number=issue.row_number,
                field=issue.field,
                message=issue.message,
                raw_value=issue.raw_value,
            )
        )
        self.session.flush()

    def persist_sale_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        transaction_date: date,
        invoice_id: str,
        invoice_line_id: str,
        product_external_id: str,
        customer_external_id: str,
        gross_revenue: float,
        tax_amount: float,
        discount_amount: float,
        return_amount: float,
        net_revenue: float,
        quantity_sold: float,
        cogs_amount: float,
    ) -> bool:
        values: dict[str, object] = {
            "sale_fact_id": f"sale_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "transaction_date": transaction_date,
            "invoice_id": invoice_id,
            "invoice_line_id": invoice_line_id,
            "product_external_id": product_external_id,
            "customer_external_id": customer_external_id,
            "gross_revenue": gross_revenue,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "return_amount": return_amount,
            "net_revenue": net_revenue,
            "quantity_sold": quantity_sold,
            "cogs_amount": cogs_amount,
            "imported_at": datetime.now(timezone.utc),
        }
        if self._table_has_column("imported_sale_facts", "period_ref"):
            values["period_ref"] = period_ref

        return self._insert_row(
            "imported_sale_facts",
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_financial_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        transaction_date: date,
        cash_flow_type: str,
        account_type: str,
        cash_in_amount: float,
        cash_out_amount: float,
        operating_cash_flow_amount: float,
        description: str | None,
    ) -> bool:
        values: dict[str, object] = {
            "financial_fact_id": f"fin_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "transaction_date": transaction_date,
            "cash_flow_type": cash_flow_type,
            "account_type": account_type,
            "cash_in_amount": cash_in_amount,
            "cash_out_amount": cash_out_amount,
            "operating_cash_flow_amount": operating_cash_flow_amount,
            "description": description,
            "imported_at": datetime.now(timezone.utc),
        }
        if self._table_has_column("imported_financial_facts", "period_ref"):
            values["period_ref"] = period_ref

        return self._insert_row(
            "imported_financial_facts",
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_balance_sheet_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        reference_date: date,
        current_assets: float,
        non_current_assets: float,
        cash_and_equivalents: float,
        inventory: float,
        accounts_receivable: float,
        other_current_assets: float,
        current_liabilities: float,
        non_current_liabilities: float,
        accounts_payable: float,
        total_assets: float,
        total_liabilities: float,
        equity: float,
    ) -> bool:
        table_name = "imported_balance_sheet_facts"
        values: dict[str, object] = {
            "balance_sheet_fact_id": f"bal_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "reference_date": reference_date,
            "current_assets": current_assets,
            "non_current_assets": non_current_assets,
            "cash_and_equivalents": cash_and_equivalents,
            "inventory": inventory,
            "accounts_receivable": accounts_receivable,
            "other_current_assets": other_current_assets,
            "current_liabilities": current_liabilities,
            "non_current_liabilities": non_current_liabilities,
            "accounts_payable": accounts_payable,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "equity": equity,
        }
        if self._table_has_column(table_name, "period_ref"):
            values["period_ref"] = period_ref
        if self._table_has_column(table_name, "imported_at"):
            values["imported_at"] = datetime.now(timezone.utc)

        return self._insert_row(
            table_name,
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_income_statement_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        gross_revenue: float,
        net_revenue: float,
        cogs: float,
        gross_profit: float,
        operating_expenses: float,
        ebit: float,
        depreciation: float,
        amortization: float,
        ebitda: float,
        financial_income: float,
        financial_expense: float,
        income_before_tax: float,
        income_tax: float,
        net_income: float,
        nopat: float,
    ) -> bool:
        table_name = "imported_income_statement_facts"
        values: dict[str, object] = {
            "income_statement_fact_id": f"is_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "gross_revenue": gross_revenue,
            "net_revenue": net_revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "operating_expenses": operating_expenses,
            "ebit": ebit,
            "depreciation": depreciation,
            "amortization": amortization,
            "ebitda": ebitda,
            "financial_income": financial_income,
            "financial_expense": financial_expense,
            "income_before_tax": income_before_tax,
            "income_tax": income_tax,
            "net_income": net_income,
            "nopat": nopat,
        }
        if self._table_has_column(table_name, "period_ref"):
            values["period_ref"] = period_ref
        if self._table_has_column(table_name, "imported_at"):
            values["imported_at"] = datetime.now(timezone.utc)

        return self._insert_row(
            table_name,
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_accounts_receivable_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        customer_id: str,
        invoice_number: str,
        issue_date: date,
        due_date: date,
        payment_date: date | None,
        amount: float,
        received_amount: float,
        outstanding_amount: float,
        status: str,
        aging_days: int,
    ) -> bool:
        table_name = "imported_accounts_receivable_facts"
        values: dict[str, object] = {
            "accounts_receivable_fact_id": f"ar_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "customer_id": customer_id,
            "invoice_number": invoice_number,
            "issue_date": issue_date,
            "due_date": due_date,
            "payment_date": payment_date,
            "amount": amount,
            "received_amount": received_amount,
            "outstanding_amount": outstanding_amount,
            "status": status,
            "aging_days": aging_days,
        }
        if self._table_has_column(table_name, "period_ref"):
            values["period_ref"] = period_ref
        if self._table_has_column(table_name, "imported_at"):
            values["imported_at"] = datetime.now(timezone.utc)

        return self._insert_row(
            table_name,
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_accounts_payable_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        supplier_id: str,
        invoice_number: str,
        issue_date: date,
        due_date: date,
        payment_date: date | None,
        amount: float,
        paid_amount: float,
        outstanding_amount: float,
        status: str,
        aging_days: int,
    ) -> bool:
        table_name = "imported_accounts_payable_facts"
        values: dict[str, object] = {
            "accounts_payable_fact_id": f"ap_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "supplier_id": supplier_id,
            "invoice_number": invoice_number,
            "issue_date": issue_date,
            "due_date": due_date,
            "payment_date": payment_date,
            "amount": amount,
            "paid_amount": paid_amount,
            "outstanding_amount": outstanding_amount,
            "status": status,
            "aging_days": aging_days,
        }
        if self._table_has_column(table_name, "period_ref"):
            values["period_ref"] = period_ref
        if self._table_has_column(table_name, "imported_at"):
            values["imported_at"] = datetime.now(timezone.utc)

        return self._insert_row(
            table_name,
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_inventory_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        product_id: str,
        warehouse_id: str,
        snapshot_date: date,
        opening_quantity: float,
        closing_quantity: float,
        average_quantity: float,
        average_cost: float,
        inventory_value: float,
        stock_turnover: float,
        days_in_inventory: float,
    ) -> bool:
        table_name = "imported_inventory_facts"
        values: dict[str, object] = {
            "inventory_fact_id": f"inv_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "snapshot_date": snapshot_date,
            "opening_quantity": opening_quantity,
            "closing_quantity": closing_quantity,
            "average_quantity": average_quantity,
            "average_cost": average_cost,
            "inventory_value": inventory_value,
            "stock_turnover": stock_turnover,
            "days_in_inventory": days_in_inventory,
        }
        if self._table_has_column(table_name, "period_ref"):
            values["period_ref"] = period_ref
        if self._table_has_column(table_name, "imported_at"):
            values["imported_at"] = datetime.now(timezone.utc)

        return self._insert_row(
            table_name,
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def persist_hr_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        period_ref: str,
        employee_count: int,
        active_employee_count: int,
        terminated_employee_count: int,
        payroll_amount: float,
        average_salary: float,
        hours_worked: float,
    ) -> bool:
        table_name = "imported_hr_facts"
        values: dict[str, object] = {
            "hr_fact_id": f"hr_{uuid4().hex[:16]}",
            "import_job_id": job_id,
            "company_id": company_id,
            "source_system": source_system,
            "source_record_id": source_record_id,
            "employee_count": employee_count,
            "active_employee_count": active_employee_count,
            "terminated_employee_count": terminated_employee_count,
            "payroll_amount": payroll_amount,
            "average_salary": average_salary,
            "hours_worked": hours_worked,
        }
        if self._table_has_column(table_name, "period_ref"):
            values["period_ref"] = period_ref
        if self._table_has_column(table_name, "imported_at"):
            values["imported_at"] = datetime.now(timezone.utc)

        return self._insert_row(
            table_name,
            values,
            conflict_columns=("company_id", "source_system", "source_record_id"),
        )

    def publish_ingest_completed(
        self,
        *,
        job_id: str,
        company_id: str,
        payload: dict[str, object],
    ) -> IntegrationEvent:
        event = IntegrationEvent(topic="ingest.completed.v1", payload=payload)
        self.session.add(
            ImportPublishedEventModel(
                event_id=event.event_id,
                import_job_id=job_id,
                company_id=company_id,
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event

    def _table_has_column(self, table_name: str, column_name: str) -> bool:
        columns = self._table_columns_cache.get(table_name)
        if columns is None:
            inspector = inspect(self.session.connection())
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            self._table_columns_cache[table_name] = columns
        return column_name in columns

    def _insert_row(
        self,
        table_name: str,
        values: dict[str, object],
        *,
        conflict_columns: tuple[str, ...] | None = None,
    ) -> bool:
        columns = ", ".join(values.keys())
        placeholders = ", ".join(f":{key}" for key in values)
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        if conflict_columns:
            sql += f" ON CONFLICT ({', '.join(conflict_columns)}) DO NOTHING"
        result = self.session.execute(text(sql), values)
        cursor_result = cast(CursorResult[object], result)
        return bool(cursor_result.rowcount and cursor_result.rowcount > 0)
