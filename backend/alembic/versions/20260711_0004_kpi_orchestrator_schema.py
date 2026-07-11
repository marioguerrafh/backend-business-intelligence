"""kpi orchestrator schema

Revision ID: 20260711_0004
Revises: 20260710_0003
Create Date: 2026-07-11 00:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260711_0004"
down_revision = "20260710_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("kpi_results", sa.Column("period_grain", sa.String(length=16), nullable=True))
    op.add_column("kpi_results", sa.Column("formula_id", sa.String(length=128), nullable=True))
    op.add_column("kpi_results", sa.Column("confidence_score", sa.Float(), nullable=True))
    op.add_column("kpi_results", sa.Column("orchestrator_run_id", sa.String(length=64), nullable=True))

    op.execute("UPDATE kpi_results SET period_grain = 'month' WHERE period_grain IS NULL")
    op.alter_column("kpi_results", "period_grain", existing_type=sa.String(length=16), nullable=False)
    op.create_index("ix_kpi_results_orchestrator_run_id", "kpi_results", ["orchestrator_run_id"])

    op.create_table(
        "orchestrator_runs",
        sa.Column("orchestrator_run_pk", sa.String(length=64), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("pipeline_stage", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("orchestrator_run_pk"),
        sa.UniqueConstraint(
            "company_id",
            "period_ref",
            "orchestrator_run_id",
            name="uq_orchestrator_run_company_period_run",
        ),
    )
    op.create_index("ix_orchestrator_runs_company_id", "orchestrator_runs", ["company_id"])
    op.create_index("ix_orchestrator_runs_period_ref", "orchestrator_runs", ["period_ref"])
    op.create_index("ix_orchestrator_runs_company_period", "orchestrator_runs", ["company_id", "period_ref"])

    op.create_table(
        "kpi_orchestrator_audit_logs",
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("formula_id", sa.String(length=128), nullable=False),
        sa.Column("kpi_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("execution_steps_json", sa.Text(), nullable=False),
        sa.Column("inputs_used_json", sa.Text(), nullable=False),
        sa.Column("result_value", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index("ix_kpi_orchestrator_audit_logs_company_id", "kpi_orchestrator_audit_logs", ["company_id"])
    op.create_index("ix_kpi_orchestrator_audit_logs_period_ref", "kpi_orchestrator_audit_logs", ["period_ref"])
    op.create_index(
        "ix_kpi_orchestrator_audit_logs_orchestrator_run_id",
        "kpi_orchestrator_audit_logs",
        ["orchestrator_run_id"],
    )
    op.create_index(
        "ix_orchestrator_audit_company_period",
        "kpi_orchestrator_audit_logs",
        ["company_id", "period_ref"],
    )

    op.create_table(
        "kpi_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_kpi_published_events_company_id", "kpi_published_events", ["company_id"])
    op.create_index("ix_kpi_published_events_period_ref", "kpi_published_events", ["period_ref"])
    op.create_index("ix_kpi_published_events_orchestrator_run_id", "kpi_published_events", ["orchestrator_run_id"])
    op.create_index(
        "ix_kpi_published_events_company_period",
        "kpi_published_events",
        ["company_id", "period_ref"],
    )


def downgrade() -> None:
    op.drop_index("ix_kpi_published_events_company_period", table_name="kpi_published_events")
    op.drop_index("ix_kpi_published_events_orchestrator_run_id", table_name="kpi_published_events")
    op.drop_index("ix_kpi_published_events_period_ref", table_name="kpi_published_events")
    op.drop_index("ix_kpi_published_events_company_id", table_name="kpi_published_events")
    op.drop_table("kpi_published_events")

    op.drop_index("ix_orchestrator_audit_company_period", table_name="kpi_orchestrator_audit_logs")
    op.drop_index("ix_kpi_orchestrator_audit_logs_orchestrator_run_id", table_name="kpi_orchestrator_audit_logs")
    op.drop_index("ix_kpi_orchestrator_audit_logs_period_ref", table_name="kpi_orchestrator_audit_logs")
    op.drop_index("ix_kpi_orchestrator_audit_logs_company_id", table_name="kpi_orchestrator_audit_logs")
    op.drop_table("kpi_orchestrator_audit_logs")

    op.drop_index("ix_orchestrator_runs_company_period", table_name="orchestrator_runs")
    op.drop_index("ix_orchestrator_runs_period_ref", table_name="orchestrator_runs")
    op.drop_index("ix_orchestrator_runs_company_id", table_name="orchestrator_runs")
    op.drop_table("orchestrator_runs")

    op.drop_index("ix_kpi_results_orchestrator_run_id", table_name="kpi_results")
    op.drop_column("kpi_results", "orchestrator_run_id")
    op.drop_column("kpi_results", "confidence_score")
    op.drop_column("kpi_results", "formula_id")
    op.drop_column("kpi_results", "period_grain")
