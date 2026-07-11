"""rule engine schema

Revision ID: 20260711_0005
Revises: 20260711_0004
Create Date: 2026-07-11 01:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260711_0005"
down_revision = "20260711_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rule_results",
        sa.Column("rule_result_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("kpi_id", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.String(length=8), nullable=False),
        sa.Column("alert_title", sa.String(length=255), nullable=False),
        sa.Column("alert_description", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("rule_result_id"),
        sa.UniqueConstraint(
            "company_id",
            "period_ref",
            "kpi_id",
            "rule_id",
            name="uq_rule_results_dedup",
        ),
    )
    op.create_index("ix_rule_results_company_id", "rule_results", ["company_id"])
    op.create_index("ix_rule_results_period_ref", "rule_results", ["period_ref"])
    op.create_index("ix_rule_results_kpi_id", "rule_results", ["kpi_id"])
    op.create_index("ix_rule_results_rule_id", "rule_results", ["rule_id"])
    op.create_index("ix_rule_results_orchestrator_run_id", "rule_results", ["orchestrator_run_id"])
    op.create_index("ix_rule_results_company_period", "rule_results", ["company_id", "period_ref"])

    op.create_table(
        "rule_audit_logs",
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("kpi_id", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("expression", sa.Text(), nullable=False),
        sa.Column("trace_json", sa.Text(), nullable=False),
        sa.Column("fired", sa.String(length=5), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index("ix_rule_audit_logs_company_id", "rule_audit_logs", ["company_id"])
    op.create_index("ix_rule_audit_logs_period_ref", "rule_audit_logs", ["period_ref"])
    op.create_index("ix_rule_audit_logs_kpi_id", "rule_audit_logs", ["kpi_id"])
    op.create_index("ix_rule_audit_logs_orchestrator_run_id", "rule_audit_logs", ["orchestrator_run_id"])
    op.create_index("ix_rule_audit_company_period", "rule_audit_logs", ["company_id", "period_ref"])

    op.create_table(
        "rule_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("rule_id", sa.String(length=128), nullable=False),
        sa.Column("kpi_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_rule_published_events_company_id", "rule_published_events", ["company_id"])
    op.create_index("ix_rule_published_events_period_ref", "rule_published_events", ["period_ref"])
    op.create_index("ix_rule_published_company_period", "rule_published_events", ["company_id", "period_ref"])


def downgrade() -> None:
    op.drop_index("ix_rule_published_company_period", table_name="rule_published_events")
    op.drop_index("ix_rule_published_events_period_ref", table_name="rule_published_events")
    op.drop_index("ix_rule_published_events_company_id", table_name="rule_published_events")
    op.drop_table("rule_published_events")

    op.drop_index("ix_rule_audit_company_period", table_name="rule_audit_logs")
    op.drop_index("ix_rule_audit_logs_orchestrator_run_id", table_name="rule_audit_logs")
    op.drop_index("ix_rule_audit_logs_kpi_id", table_name="rule_audit_logs")
    op.drop_index("ix_rule_audit_logs_period_ref", table_name="rule_audit_logs")
    op.drop_index("ix_rule_audit_logs_company_id", table_name="rule_audit_logs")
    op.drop_table("rule_audit_logs")

    op.drop_index("ix_rule_results_company_period", table_name="rule_results")
    op.drop_index("ix_rule_results_orchestrator_run_id", table_name="rule_results")
    op.drop_index("ix_rule_results_rule_id", table_name="rule_results")
    op.drop_index("ix_rule_results_kpi_id", table_name="rule_results")
    op.drop_index("ix_rule_results_period_ref", table_name="rule_results")
    op.drop_index("ix_rule_results_company_id", table_name="rule_results")
    op.drop_table("rule_results")
