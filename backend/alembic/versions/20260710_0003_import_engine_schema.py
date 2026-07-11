"""import engine schema

Revision ID: 20260710_0003
Revises: 20260710_0002
Create Date: 2026-07-10 02:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260710_0003"
down_revision = "20260710_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("template", sa.String(length=32), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("canonical_schema_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("imported_rows", sa.Integer(), nullable=False),
        sa.Column("failed_rows", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("import_job_id"),
    )
    op.create_index("ix_import_jobs_company_id", "import_jobs", ["company_id"])
    op.create_index("ix_import_jobs_company_template", "import_jobs", ["company_id", "template"])

    op.create_table(
        "import_inconsistencies",
        sa.Column("inconsistency_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("inconsistency_id"),
    )
    op.create_index("ix_import_inconsistencies_company_id", "import_inconsistencies", ["company_id"])
    op.create_index("ix_import_inconsistencies_import_job_id", "import_inconsistencies", ["import_job_id"])
    op.create_index("ix_import_inconsistencies_job", "import_inconsistencies", ["import_job_id"])

    op.create_table(
        "imported_sale_facts",
        sa.Column("sale_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("invoice_id", sa.String(length=128), nullable=False),
        sa.Column("invoice_line_id", sa.String(length=128), nullable=False),
        sa.Column("product_external_id", sa.String(length=255), nullable=False),
        sa.Column("customer_external_id", sa.String(length=255), nullable=False),
        sa.Column("gross_revenue", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("discount_amount", sa.Float(), nullable=False),
        sa.Column("return_amount", sa.Float(), nullable=False),
        sa.Column("net_revenue", sa.Float(), nullable=False),
        sa.Column("quantity_sold", sa.Float(), nullable=False),
        sa.Column("cogs_amount", sa.Float(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("sale_fact_id"),
    )
    op.create_index("ix_imported_sale_facts_company_id", "imported_sale_facts", ["company_id"])
    op.create_index("ix_imported_sale_facts_import_job_id", "imported_sale_facts", ["import_job_id"])
    op.create_index("ix_import_sales_job", "imported_sale_facts", ["import_job_id"])

    op.create_table(
        "imported_financial_facts",
        sa.Column("financial_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("cash_flow_type", sa.String(length=64), nullable=False),
        sa.Column("account_type", sa.String(length=64), nullable=False),
        sa.Column("cash_in_amount", sa.Float(), nullable=False),
        sa.Column("cash_out_amount", sa.Float(), nullable=False),
        sa.Column("operating_cash_flow_amount", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("financial_fact_id"),
    )
    op.create_index("ix_imported_financial_facts_company_id", "imported_financial_facts", ["company_id"])
    op.create_index("ix_imported_financial_facts_import_job_id", "imported_financial_facts", ["import_job_id"])
    op.create_index("ix_import_financial_job", "imported_financial_facts", ["import_job_id"])

    op.create_table(
        "import_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_import_published_events_company_id", "import_published_events", ["company_id"])
    op.create_index("ix_import_published_events_import_job_id", "import_published_events", ["import_job_id"])
    op.create_index("ix_import_published_events_job", "import_published_events", ["import_job_id"])


def downgrade() -> None:
    op.drop_index("ix_import_published_events_job", table_name="import_published_events")
    op.drop_index("ix_import_published_events_import_job_id", table_name="import_published_events")
    op.drop_index("ix_import_published_events_company_id", table_name="import_published_events")
    op.drop_table("import_published_events")

    op.drop_index("ix_import_financial_job", table_name="imported_financial_facts")
    op.drop_index("ix_imported_financial_facts_import_job_id", table_name="imported_financial_facts")
    op.drop_index("ix_imported_financial_facts_company_id", table_name="imported_financial_facts")
    op.drop_table("imported_financial_facts")

    op.drop_index("ix_import_sales_job", table_name="imported_sale_facts")
    op.drop_index("ix_imported_sale_facts_import_job_id", table_name="imported_sale_facts")
    op.drop_index("ix_imported_sale_facts_company_id", table_name="imported_sale_facts")
    op.drop_table("imported_sale_facts")

    op.drop_index("ix_import_inconsistencies_job", table_name="import_inconsistencies")
    op.drop_index("ix_import_inconsistencies_import_job_id", table_name="import_inconsistencies")
    op.drop_index("ix_import_inconsistencies_company_id", table_name="import_inconsistencies")
    op.drop_table("import_inconsistencies")

    op.drop_index("ix_import_jobs_company_template", table_name="import_jobs")
    op.drop_index("ix_import_jobs_company_id", table_name="import_jobs")
    op.drop_table("import_jobs")
