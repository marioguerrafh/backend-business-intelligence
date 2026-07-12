from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class ImportJobModel(Base):
    __tablename__ = "import_jobs"

    import_job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    template: Mapped[str] = mapped_column(String(32), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportInconsistencyModel(Base):
    __tablename__ = "import_inconsistencies"

    inconsistency_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedSaleFactModel(Base):
    __tablename__ = "imported_sale_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_sale_facts_company_source_record",
        ),
    )

    sale_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    invoice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_line_id: Mapped[str] = mapped_column(String(128), nullable=False)
    product_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    gross_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Float, nullable=False)
    return_amount: Mapped[float] = mapped_column(Float, nullable=False)
    net_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_sold: Mapped[float] = mapped_column(Float, nullable=False)
    cogs_amount: Mapped[float] = mapped_column(Float, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedFinancialFactModel(Base):
    __tablename__ = "imported_financial_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_financial_facts_company_source_record",
        ),
    )

    financial_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    cash_flow_type: Mapped[str] = mapped_column(String(64), nullable=False)
    account_type: Mapped[str] = mapped_column(String(64), nullable=False)
    cash_in_amount: Mapped[float] = mapped_column(Float, nullable=False)
    cash_out_amount: Mapped[float] = mapped_column(Float, nullable=False)
    operating_cash_flow_amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportPublishedEventModel(Base):
    __tablename__ = "import_published_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImportedBalanceSheetFactModel(Base):
    __tablename__ = "imported_balance_sheet_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_balance_sheet_company_source_record",
        ),
    )

    balance_sheet_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_assets: Mapped[float] = mapped_column(Float, nullable=False)
    non_current_assets: Mapped[float] = mapped_column(Float, nullable=False)
    cash_and_equivalents: Mapped[float] = mapped_column(Float, nullable=False)
    inventory: Mapped[float] = mapped_column(Float, nullable=False)
    accounts_receivable: Mapped[float] = mapped_column(Float, nullable=False)
    other_current_assets: Mapped[float] = mapped_column(Float, nullable=False)
    current_liabilities: Mapped[float] = mapped_column(Float, nullable=False)
    non_current_liabilities: Mapped[float] = mapped_column(Float, nullable=False)
    accounts_payable: Mapped[float] = mapped_column(Float, nullable=False)
    total_assets: Mapped[float] = mapped_column(Float, nullable=False)
    total_liabilities: Mapped[float] = mapped_column(Float, nullable=False)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedIncomeStatementFactModel(Base):
    __tablename__ = "imported_income_statement_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_income_statement_company_source_record",
        ),
    )

    income_statement_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    gross_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    net_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    cogs: Mapped[float] = mapped_column(Float, nullable=False)
    gross_profit: Mapped[float] = mapped_column(Float, nullable=False)
    operating_expenses: Mapped[float] = mapped_column(Float, nullable=False)
    ebit: Mapped[float] = mapped_column(Float, nullable=False)
    depreciation: Mapped[float] = mapped_column(Float, nullable=False)
    amortization: Mapped[float] = mapped_column(Float, nullable=False)
    ebitda: Mapped[float] = mapped_column(Float, nullable=False)
    financial_income: Mapped[float] = mapped_column(Float, nullable=False)
    financial_expense: Mapped[float] = mapped_column(Float, nullable=False)
    income_before_tax: Mapped[float] = mapped_column(Float, nullable=False)
    income_tax: Mapped[float] = mapped_column(Float, nullable=False)
    net_income: Mapped[float] = mapped_column(Float, nullable=False)
    nopat: Mapped[float] = mapped_column(Float, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedAccountsReceivableFactModel(Base):
    __tablename__ = "imported_accounts_receivable_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_accounts_receivable_company_source_record",
        ),
    )

    accounts_receivable_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    received_amount: Mapped[float] = mapped_column(Float, nullable=False)
    outstanding_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    aging_days: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedAccountsPayableFactModel(Base):
    __tablename__ = "imported_accounts_payable_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_accounts_payable_company_source_record",
        ),
    )

    accounts_payable_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    outstanding_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    aging_days: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedInventoryFactModel(Base):
    __tablename__ = "imported_inventory_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_inventory_company_source_record",
        ),
    )

    inventory_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String(128), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    opening_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    closing_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    average_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    average_cost: Mapped[float] = mapped_column(Float, nullable=False)
    inventory_value: Mapped[float] = mapped_column(Float, nullable=False)
    stock_turnover: Mapped[float] = mapped_column(Float, nullable=False)
    days_in_inventory: Mapped[float] = mapped_column(Float, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ImportedHrFactModel(Base):
    __tablename__ = "imported_hr_facts"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_hr_company_source_record",
        ),
    )

    hr_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    period_ref: Mapped[str] = mapped_column(String(7), nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    active_employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    terminated_employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    payroll_amount: Mapped[float] = mapped_column(Float, nullable=False)
    average_salary: Mapped[float] = mapped_column(Float, nullable=False)
    hours_worked: Mapped[float] = mapped_column(Float, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


Index("ix_import_jobs_company_template", ImportJobModel.company_id, ImportJobModel.template)
Index("ix_import_inconsistencies_job", ImportInconsistencyModel.import_job_id)
Index("ix_import_sales_job", ImportedSaleFactModel.import_job_id)
Index("ix_import_financial_job", ImportedFinancialFactModel.import_job_id)
Index("ix_import_published_events_job", ImportPublishedEventModel.import_job_id)
Index("ix_import_balance_sheet_job", ImportedBalanceSheetFactModel.import_job_id)
Index("ix_import_income_statement_job", ImportedIncomeStatementFactModel.import_job_id)
Index("ix_import_accounts_receivable_job", ImportedAccountsReceivableFactModel.import_job_id)
Index("ix_import_accounts_payable_job", ImportedAccountsPayableFactModel.import_job_id)
Index("ix_import_inventory_job", ImportedInventoryFactModel.import_job_id)
Index("ix_import_hr_job", ImportedHrFactModel.import_job_id)
