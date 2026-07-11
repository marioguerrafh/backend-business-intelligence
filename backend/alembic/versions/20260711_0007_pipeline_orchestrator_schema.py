"""pipeline orchestrator schema

Revision ID: 20260711_0007
Revises: 20260711_0006
Create Date: 2026-07-11 14:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260711_0007"
down_revision = "20260711_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("template", sa.String(length=32), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("retry_of_pipeline_run_id", sa.String(length=64), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("pipeline_run_id"),
    )
    op.create_index("ix_pipeline_runs_company_id", "pipeline_runs", ["company_id"])
    op.create_index("ix_pipeline_runs_import_job_id", "pipeline_runs", ["import_job_id"])
    op.create_index("ix_pipeline_runs_company_job", "pipeline_runs", ["company_id", "import_job_id"])

    op.create_table(
        "pipeline_steps",
        sa.Column("step_id", sa.String(length=64), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("import_job_id", sa.String(length=64), nullable=False),
        sa.Column("step_name", sa.String(length=64), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("step_id"),
    )
    op.create_index("ix_pipeline_steps_pipeline_run_id", "pipeline_steps", ["pipeline_run_id"])
    op.create_index("ix_pipeline_steps_company_id", "pipeline_steps", ["company_id"])
    op.create_index("ix_pipeline_steps_import_job_id", "pipeline_steps", ["import_job_id"])
    op.create_index("ix_pipeline_steps_run_order", "pipeline_steps", ["pipeline_run_id", "step_order"])
    op.create_index("ix_pipeline_steps_company_job", "pipeline_steps", ["company_id", "import_job_id"])

    op.create_table(
        "pipeline_logs",
        sa.Column("log_id", sa.String(length=64), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("step_name", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index("ix_pipeline_logs_pipeline_run_id", "pipeline_logs", ["pipeline_run_id"])
    op.create_index("ix_pipeline_logs_company_id", "pipeline_logs", ["company_id"])
    op.create_index("ix_pipeline_logs_run", "pipeline_logs", ["pipeline_run_id"])

    op.create_table(
        "pipeline_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_pipeline_events_pipeline_run_id", "pipeline_events", ["pipeline_run_id"])
    op.create_index("ix_pipeline_events_company_id", "pipeline_events", ["company_id"])
    op.create_index("ix_pipeline_events_run", "pipeline_events", ["pipeline_run_id"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_events_run", table_name="pipeline_events")
    op.drop_index("ix_pipeline_events_company_id", table_name="pipeline_events")
    op.drop_index("ix_pipeline_events_pipeline_run_id", table_name="pipeline_events")
    op.drop_table("pipeline_events")

    op.drop_index("ix_pipeline_logs_run", table_name="pipeline_logs")
    op.drop_index("ix_pipeline_logs_company_id", table_name="pipeline_logs")
    op.drop_index("ix_pipeline_logs_pipeline_run_id", table_name="pipeline_logs")
    op.drop_table("pipeline_logs")

    op.drop_index("ix_pipeline_steps_company_job", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_run_order", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_import_job_id", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_company_id", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_pipeline_run_id", table_name="pipeline_steps")
    op.drop_table("pipeline_steps")

    op.drop_index("ix_pipeline_runs_company_job", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_import_job_id", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_company_id", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
