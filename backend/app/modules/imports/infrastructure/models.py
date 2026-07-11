from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text
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

    sale_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
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

    financial_fact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
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


Index("ix_import_jobs_company_template", ImportJobModel.company_id, ImportJobModel.template)
Index("ix_import_inconsistencies_job", ImportInconsistencyModel.import_job_id)
Index("ix_import_sales_job", ImportedSaleFactModel.import_job_id)
Index("ix_import_financial_job", ImportedFinancialFactModel.import_job_id)
Index("ix_import_published_events_job", ImportPublishedEventModel.import_job_id)
