"""import engine v2 canonical facts

Revision ID: 20260712_0008
Revises: 20260711_0007
Create Date: 2026-07-12 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260712_0008"
down_revision = "20260711_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "imported_sale_facts",
        sa.Column("period_ref", sa.String(length=7), nullable=False, server_default="1970-01"),
    )
    op.alter_column("imported_sale_facts", "period_ref", server_default=None)

    op.add_column(
        "imported_financial_facts",
        sa.Column("period_ref", sa.String(length=7), nullable=False, server_default="1970-01"),
    )
    op.alter_column("imported_financial_facts", "period_ref", server_default=None)

    op.create_unique_constraint(
        "uq_imported_sale_facts_company_source_record",
        "imported_sale_facts",
        ["company_id", "source_system", "source_record_id"],
    )
    op.create_unique_constraint(
        "uq_imported_financial_facts_company_source_record",
        "imported_financial_facts",
        ["company_id", "source_system", "source_record_id"],
    )

    op.create_table(
        "imported_balance_sheet_facts",
        sa.Column("balance_sheet_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("period_ref", sa.String(length=7), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("current_assets", sa.Float(), nullable=False),
        sa.Column("non_current_assets", sa.Float(), nullable=False),
        sa.Column("cash_and_equivalents", sa.Float(), nullable=False),
        sa.Column("inventory", sa.Float(), nullable=False),
        sa.Column("accounts_receivable", sa.Float(), nullable=False),
        sa.Column("other_current_assets", sa.Float(), nullable=False),
        sa.Column("current_liabilities", sa.Float(), nullable=False),
        sa.Column("non_current_liabilities", sa.Float(), nullable=False),
        sa.Column("accounts_payable", sa.Float(), nullable=False),
        sa.Column("total_assets", sa.Float(), nullable=False),
        sa.Column("total_liabilities", sa.Float(), nullable=False),
        sa.Column("equity", sa.Float(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("balance_sheet_fact_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_balance_sheet_company_source_record",
        ),
    )
    op.create_index("ix_imported_balance_sheet_facts_company_id", "imported_balance_sheet_facts", ["company_id"])
    op.create_index("ix_imported_balance_sheet_facts_import_job_id", "imported_balance_sheet_facts", ["import_job_id"])
    op.create_index("ix_import_balance_sheet_job", "imported_balance_sheet_facts", ["import_job_id"])

    op.create_table(
        "imported_income_statement_facts",
        sa.Column("income_statement_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("period_ref", sa.String(length=7), nullable=False),
        sa.Column("gross_revenue", sa.Float(), nullable=False),
        sa.Column("net_revenue", sa.Float(), nullable=False),
        sa.Column("cogs", sa.Float(), nullable=False),
        sa.Column("gross_profit", sa.Float(), nullable=False),
        sa.Column("operating_expenses", sa.Float(), nullable=False),
        sa.Column("ebit", sa.Float(), nullable=False),
        sa.Column("depreciation", sa.Float(), nullable=False),
        sa.Column("amortization", sa.Float(), nullable=False),
        sa.Column("ebitda", sa.Float(), nullable=False),
        sa.Column("financial_income", sa.Float(), nullable=False),
        sa.Column("financial_expense", sa.Float(), nullable=False),
        sa.Column("income_before_tax", sa.Float(), nullable=False),
        sa.Column("income_tax", sa.Float(), nullable=False),
        sa.Column("net_income", sa.Float(), nullable=False),
        sa.Column("nopat", sa.Float(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("income_statement_fact_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_income_statement_company_source_record",
        ),
    )
    op.create_index("ix_imported_income_statement_facts_company_id", "imported_income_statement_facts", ["company_id"])
    op.create_index("ix_imported_income_statement_facts_import_job_id", "imported_income_statement_facts", ["import_job_id"])
    op.create_index("ix_import_income_statement_job", "imported_income_statement_facts", ["import_job_id"])

    op.create_table(
        "imported_accounts_receivable_facts",
        sa.Column("accounts_receivable_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("period_ref", sa.String(length=7), nullable=False),
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.Column("invoice_number", sa.String(length=128), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("received_amount", sa.Float(), nullable=False),
        sa.Column("outstanding_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("aging_days", sa.Integer(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("accounts_receivable_fact_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_accounts_receivable_company_source_record",
        ),
    )
    op.create_index(
        "ix_imported_accounts_receivable_facts_company_id", "imported_accounts_receivable_facts", ["company_id"]
    )
    op.create_index(
        "ix_imported_accounts_receivable_facts_import_job_id",
        "imported_accounts_receivable_facts",
        ["import_job_id"],
    )
    op.create_index("ix_import_accounts_receivable_job", "imported_accounts_receivable_facts", ["import_job_id"])

    op.create_table(
        "imported_accounts_payable_facts",
        sa.Column("accounts_payable_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("period_ref", sa.String(length=7), nullable=False),
        sa.Column("supplier_id", sa.String(length=128), nullable=False),
        sa.Column("invoice_number", sa.String(length=128), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), nullable=False),
        sa.Column("outstanding_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("aging_days", sa.Integer(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("accounts_payable_fact_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_accounts_payable_company_source_record",
        ),
    )
    op.create_index("ix_imported_accounts_payable_facts_company_id", "imported_accounts_payable_facts", ["company_id"])
    op.create_index("ix_imported_accounts_payable_facts_import_job_id", "imported_accounts_payable_facts", ["import_job_id"])
    op.create_index("ix_import_accounts_payable_job", "imported_accounts_payable_facts", ["import_job_id"])

    op.create_table(
        "imported_inventory_facts",
        sa.Column("inventory_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("period_ref", sa.String(length=7), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("warehouse_id", sa.String(length=128), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("opening_quantity", sa.Float(), nullable=False),
        sa.Column("closing_quantity", sa.Float(), nullable=False),
        sa.Column("average_quantity", sa.Float(), nullable=False),
        sa.Column("average_cost", sa.Float(), nullable=False),
        sa.Column("inventory_value", sa.Float(), nullable=False),
        sa.Column("stock_turnover", sa.Float(), nullable=False),
        sa.Column("days_in_inventory", sa.Float(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("inventory_fact_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_inventory_company_source_record",
        ),
    )
    op.create_index("ix_imported_inventory_facts_company_id", "imported_inventory_facts", ["company_id"])
    op.create_index("ix_imported_inventory_facts_import_job_id", "imported_inventory_facts", ["import_job_id"])
    op.create_index("ix_import_inventory_job", "imported_inventory_facts", ["import_job_id"])

    op.create_table(
        "imported_hr_facts",
        sa.Column("hr_fact_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("period_ref", sa.String(length=7), nullable=False),
        sa.Column("employee_count", sa.Integer(), nullable=False),
        sa.Column("active_employee_count", sa.Integer(), nullable=False),
        sa.Column("terminated_employee_count", sa.Integer(), nullable=False),
        sa.Column("payroll_amount", sa.Float(), nullable=False),
        sa.Column("average_salary", sa.Float(), nullable=False),
        sa.Column("hours_worked", sa.Float(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("hr_fact_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_imported_hr_company_source_record",
        ),
    )
    op.create_index("ix_imported_hr_facts_company_id", "imported_hr_facts", ["company_id"])
    op.create_index("ix_imported_hr_facts_import_job_id", "imported_hr_facts", ["import_job_id"])
    op.create_index("ix_import_hr_job", "imported_hr_facts", ["import_job_id"])


def downgrade() -> None:
    op.drop_index("ix_import_hr_job", table_name="imported_hr_facts")
    op.drop_index("ix_imported_hr_facts_import_job_id", table_name="imported_hr_facts")
    op.drop_index("ix_imported_hr_facts_company_id", table_name="imported_hr_facts")
    op.drop_table("imported_hr_facts")

    op.drop_index("ix_import_inventory_job", table_name="imported_inventory_facts")
    op.drop_index("ix_imported_inventory_facts_import_job_id", table_name="imported_inventory_facts")
    op.drop_index("ix_imported_inventory_facts_company_id", table_name="imported_inventory_facts")
    op.drop_table("imported_inventory_facts")

    op.drop_index("ix_import_accounts_payable_job", table_name="imported_accounts_payable_facts")
    op.drop_index("ix_imported_accounts_payable_facts_import_job_id", table_name="imported_accounts_payable_facts")
    op.drop_index("ix_imported_accounts_payable_facts_company_id", table_name="imported_accounts_payable_facts")
    op.drop_table("imported_accounts_payable_facts")

    op.drop_index("ix_import_accounts_receivable_job", table_name="imported_accounts_receivable_facts")
    op.drop_index("ix_imported_accounts_receivable_facts_import_job_id", table_name="imported_accounts_receivable_facts")
    op.drop_index("ix_imported_accounts_receivable_facts_company_id", table_name="imported_accounts_receivable_facts")
    op.drop_table("imported_accounts_receivable_facts")

    op.drop_index("ix_import_income_statement_job", table_name="imported_income_statement_facts")
    op.drop_index("ix_imported_income_statement_facts_import_job_id", table_name="imported_income_statement_facts")
    op.drop_index("ix_imported_income_statement_facts_company_id", table_name="imported_income_statement_facts")
    op.drop_table("imported_income_statement_facts")

    op.drop_index("ix_import_balance_sheet_job", table_name="imported_balance_sheet_facts")
    op.drop_index("ix_imported_balance_sheet_facts_import_job_id", table_name="imported_balance_sheet_facts")
    op.drop_index("ix_imported_balance_sheet_facts_company_id", table_name="imported_balance_sheet_facts")
    op.drop_table("imported_balance_sheet_facts")

    op.drop_constraint(
        "uq_imported_financial_facts_company_source_record",
        "imported_financial_facts",
        type_="unique",
    )
    op.drop_constraint(
        "uq_imported_sale_facts_company_source_record",
        "imported_sale_facts",
        type_="unique",
    )
    op.drop_column("imported_sale_facts", "period_ref")
    op.drop_column("imported_financial_facts", "period_ref")
