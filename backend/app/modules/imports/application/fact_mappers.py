from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re

from app.modules.imports.domain.entities import CsvRow


_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


@dataclass(slots=True, frozen=True)
class CanonicalFactRecord:
    payload: dict[str, object]
    identity: str


class _BaseFactMapper:
    template: str

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        raise NotImplementedError

    @staticmethod
    def _required(row: CsvRow, field: str) -> str:
        value = (row.data.get(field) or "").strip()
        if not value:
            raise ValueError(f"row {row.row_number}: {field} is required")
        return value

    def _company_id(self, *, command_company_id: str, row: CsvRow) -> str:
        csv_company_id = self._required(row, "company_id")
        if csv_company_id != command_company_id:
            raise ValueError(
                f"row {row.row_number}: company_id mismatch (payload={csv_company_id}, command={command_company_id})"
            )
        return csv_company_id

    def _period_ref(self, *, row: CsvRow) -> str:
        period_ref = self._required(row, "period_ref")
        if not _PERIOD_RE.match(period_ref):
            raise ValueError(f"row {row.row_number}: period_ref must use YYYY-MM")
        return period_ref

    @staticmethod
    def _decimal(row: CsvRow, field: str, *, allow_negative: bool = False) -> Decimal:
        value = (row.data.get(field) or "").strip()
        if not value:
            raise ValueError(f"row {row.row_number}: {field} is required")
        try:
            number = Decimal(value.replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(f"row {row.row_number}: invalid decimal in {field}") from exc
        if not allow_negative and number < 0:
            raise ValueError(f"row {row.row_number}: negative value is not allowed in {field}")
        return number

    @staticmethod
    def _int(row: CsvRow, field: str, *, allow_negative: bool = False) -> int:
        value = (row.data.get(field) or "").strip()
        if not value:
            raise ValueError(f"row {row.row_number}: {field} is required")
        try:
            number = int(value)
        except ValueError as exc:
            raise ValueError(f"row {row.row_number}: invalid integer in {field}") from exc
        if not allow_negative and number < 0:
            raise ValueError(f"row {row.row_number}: negative value is not allowed in {field}")
        return number

    @staticmethod
    def _date(row: CsvRow, field: str, *, required: bool = True) -> date | None:
        value = (row.data.get(field) or "").strip()
        if not value:
            if required:
                raise ValueError(f"row {row.row_number}: {field} is required")
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"row {row.row_number}: invalid ISO date in {field}") from exc

    @staticmethod
    def _validate_period_consistency(*, row: CsvRow, period_ref: str, row_date: date, date_field: str) -> None:
        expected = row_date.strftime("%Y-%m")
        if expected != period_ref:
            raise ValueError(
                f"row {row.row_number}: {date_field} ({row_date.isoformat()}) is inconsistent with period_ref ({period_ref})"
            )


class SalesMapper(_BaseFactMapper):
    template = "sales"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)
        transaction_date = self._date(row, "transaction_date")
        assert transaction_date is not None
        self._validate_period_consistency(row=row, period_ref=period_ref, row_date=transaction_date, date_field="transaction_date")

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "transaction_date": transaction_date,
            "invoice_id": self._required(row, "invoice_id"),
            "invoice_line_id": self._required(row, "invoice_line_id"),
            "product_external_id": self._required(row, "product_external_id"),
            "customer_external_id": self._required(row, "customer_external_id"),
            "gross_revenue": float(self._decimal(row, "gross_revenue")),
            "tax_amount": float(self._decimal(row, "tax_amount")),
            "discount_amount": float(self._decimal(row, "discount_amount")),
            "return_amount": float(self._decimal(row, "return_amount")),
            "net_revenue": float(self._decimal(row, "net_revenue")),
            "quantity_sold": float(self._decimal(row, "quantity_sold")),
            "cogs_amount": float(self._decimal(row, "cogs_amount")),
        }
        identity = f"{company_id}|{payload['source_record_id']}|{payload['invoice_id']}|{payload['invoice_line_id']}"
        return CanonicalFactRecord(payload=payload, identity=identity)


class CashflowMapper(_BaseFactMapper):
    template = "cashflow"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)
        transaction_date = self._date(row, "transaction_date")
        assert transaction_date is not None
        self._validate_period_consistency(row=row, period_ref=period_ref, row_date=transaction_date, date_field="transaction_date")

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "transaction_date": transaction_date,
            "cash_flow_type": self._required(row, "cash_flow_type"),
            "account_type": self._required(row, "account_type"),
            "cash_in_amount": float(self._decimal(row, "cash_in_amount")),
            "cash_out_amount": float(self._decimal(row, "cash_out_amount")),
            "operating_cash_flow_amount": float(self._decimal(row, "operating_cash_flow_amount", allow_negative=True)),
            "description": (row.data.get("description") or "").strip() or None,
        }
        identity = f"{company_id}|{payload['source_record_id']}|{payload['transaction_date'].isoformat()}|{payload['cash_flow_type']}"
        return CanonicalFactRecord(payload=payload, identity=identity)


class BalanceSheetMapper(_BaseFactMapper):
    template = "balance_sheet"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)
        reference_date = self._date(row, "reference_date")
        assert reference_date is not None
        self._validate_period_consistency(row=row, period_ref=period_ref, row_date=reference_date, date_field="reference_date")

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "reference_date": reference_date,
            "source_record_id": self._required(row, "source_record_id"),
            "current_assets": float(self._decimal(row, "current_assets")),
            "non_current_assets": float(self._decimal(row, "non_current_assets")),
            "cash_and_equivalents": float(self._decimal(row, "cash_and_equivalents")),
            "inventory": float(self._decimal(row, "inventory")),
            "accounts_receivable": float(self._decimal(row, "accounts_receivable")),
            "other_current_assets": float(self._decimal(row, "other_current_assets")),
            "current_liabilities": float(self._decimal(row, "current_liabilities")),
            "non_current_liabilities": float(self._decimal(row, "non_current_liabilities")),
            "accounts_payable": float(self._decimal(row, "accounts_payable")),
            "total_assets": float(self._decimal(row, "total_assets")),
            "total_liabilities": float(self._decimal(row, "total_liabilities")),
            "equity": float(self._decimal(row, "equity")),
        }
        identity = f"{company_id}|{period_ref}|{payload['source_record_id']}"
        return CanonicalFactRecord(payload=payload, identity=identity)


class IncomeStatementMapper(_BaseFactMapper):
    template = "income_statement"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "gross_revenue": float(self._decimal(row, "gross_revenue")),
            "net_revenue": float(self._decimal(row, "net_revenue")),
            "cogs": float(self._decimal(row, "cogs")),
            "gross_profit": float(self._decimal(row, "gross_profit")),
            "operating_expenses": float(self._decimal(row, "operating_expenses")),
            "ebit": float(self._decimal(row, "ebit")),
            "depreciation": float(self._decimal(row, "depreciation")),
            "amortization": float(self._decimal(row, "amortization")),
            "ebitda": float(self._decimal(row, "ebitda")),
            "financial_income": float(self._decimal(row, "financial_income")),
            "financial_expense": float(self._decimal(row, "financial_expense")),
            "income_before_tax": float(self._decimal(row, "income_before_tax")),
            "income_tax": float(self._decimal(row, "income_tax")),
            "net_income": float(self._decimal(row, "net_income")),
            "nopat": float(self._decimal(row, "nopat")),
        }
        identity = f"{company_id}|{period_ref}|{payload['source_record_id']}"
        return CanonicalFactRecord(payload=payload, identity=identity)


class AccountsReceivableMapper(_BaseFactMapper):
    template = "accounts_receivable"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)
        issue_date = self._date(row, "issue_date")
        due_date = self._date(row, "due_date")
        payment_date = self._date(row, "payment_date", required=False)
        assert issue_date is not None and due_date is not None
        self._validate_period_consistency(row=row, period_ref=period_ref, row_date=issue_date, date_field="issue_date")

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "customer_id": self._required(row, "customer_id"),
            "invoice_number": self._required(row, "invoice_number"),
            "issue_date": issue_date,
            "due_date": due_date,
            "payment_date": payment_date,
            "amount": float(self._decimal(row, "amount")),
            "received_amount": float(self._decimal(row, "received_amount")),
            "outstanding_amount": float(self._decimal(row, "outstanding_amount")),
            "status": self._required(row, "status"),
            "aging_days": self._int(row, "aging_days"),
        }
        identity = f"{company_id}|{payload['source_record_id']}|{payload['invoice_number']}|{payload['customer_id']}"
        return CanonicalFactRecord(payload=payload, identity=identity)


class AccountsPayableMapper(_BaseFactMapper):
    template = "accounts_payable"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)
        issue_date = self._date(row, "issue_date")
        due_date = self._date(row, "due_date")
        payment_date = self._date(row, "payment_date", required=False)
        assert issue_date is not None and due_date is not None
        self._validate_period_consistency(row=row, period_ref=period_ref, row_date=issue_date, date_field="issue_date")

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "supplier_id": self._required(row, "supplier_id"),
            "invoice_number": self._required(row, "invoice_number"),
            "issue_date": issue_date,
            "due_date": due_date,
            "payment_date": payment_date,
            "amount": float(self._decimal(row, "amount")),
            "paid_amount": float(self._decimal(row, "paid_amount")),
            "outstanding_amount": float(self._decimal(row, "outstanding_amount")),
            "status": self._required(row, "status"),
            "aging_days": self._int(row, "aging_days"),
        }
        identity = f"{company_id}|{payload['source_record_id']}|{payload['invoice_number']}|{payload['supplier_id']}"
        return CanonicalFactRecord(payload=payload, identity=identity)


class InventoryMapper(_BaseFactMapper):
    template = "inventory"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)
        snapshot_date = self._date(row, "snapshot_date")
        assert snapshot_date is not None
        self._validate_period_consistency(row=row, period_ref=period_ref, row_date=snapshot_date, date_field="snapshot_date")

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "product_id": self._required(row, "product_id"),
            "warehouse_id": self._required(row, "warehouse_id"),
            "snapshot_date": snapshot_date,
            "opening_quantity": float(self._decimal(row, "opening_quantity")),
            "closing_quantity": float(self._decimal(row, "closing_quantity")),
            "average_quantity": float(self._decimal(row, "average_quantity")),
            "average_cost": float(self._decimal(row, "average_cost")),
            "inventory_value": float(self._decimal(row, "inventory_value")),
            "stock_turnover": float(self._decimal(row, "stock_turnover")),
            "days_in_inventory": float(self._decimal(row, "days_in_inventory")),
        }
        identity = (
            f"{company_id}|{payload['source_record_id']}|{payload['product_id']}|{payload['warehouse_id']}|"
            f"{payload['snapshot_date'].isoformat()}"
        )
        return CanonicalFactRecord(payload=payload, identity=identity)


class HrMapper(_BaseFactMapper):
    template = "hr"

    def map(self, *, command_company_id: str, row: CsvRow) -> CanonicalFactRecord:
        company_id = self._company_id(command_company_id=command_company_id, row=row)
        period_ref = self._period_ref(row=row)

        payload = {
            "company_id": company_id,
            "period_ref": period_ref,
            "source_record_id": self._required(row, "source_record_id"),
            "employee_count": self._int(row, "employee_count"),
            "active_employee_count": self._int(row, "active_employee_count"),
            "terminated_employee_count": self._int(row, "terminated_employee_count"),
            "payroll_amount": float(self._decimal(row, "payroll_amount")),
            "average_salary": float(self._decimal(row, "average_salary")),
            "hours_worked": float(self._decimal(row, "hours_worked")),
        }
        if payload["active_employee_count"] > payload["employee_count"]:
            raise ValueError(
                f"row {row.row_number}: active_employee_count cannot be greater than employee_count"
            )

        identity = f"{company_id}|{period_ref}|{payload['source_record_id']}"
        return CanonicalFactRecord(payload=payload, identity=identity)
