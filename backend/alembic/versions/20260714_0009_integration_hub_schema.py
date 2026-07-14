"""integration hub schema

Revision ID: 20260714_0009
Revises: 20260712_0008
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_0009"
down_revision = "20260712_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_connections",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("credentials", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integration_connections_company_id", "integration_connections", ["company_id"])
    op.create_index("ix_integration_connections_provider", "integration_connections", ["provider"])

    op.create_table(
        "integration_sync_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("records_read", sa.Integer(), nullable=False),
        sa.Column("records_imported", sa.Integer(), nullable=False),
        sa.Column("records_failed", sa.Integer(), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_integration_sync_jobs_company_id", "integration_sync_jobs", ["company_id"])
    op.create_index("ix_integration_sync_jobs_provider", "integration_sync_jobs", ["provider"])

    op.create_table(
        "integration_logs",
        sa.Column("log_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("request_json", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index("ix_integration_logs_company_id", "integration_logs", ["company_id"])
    op.create_index("ix_integration_logs_provider", "integration_logs", ["provider"])

    op.create_table(
        "integration_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_integration_published_events_company_id", "integration_published_events", ["company_id"])
    op.create_index("ix_integration_published_events_provider", "integration_published_events", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_integration_published_events_provider", table_name="integration_published_events")
    op.drop_index("ix_integration_published_events_company_id", table_name="integration_published_events")
    op.drop_table("integration_published_events")

    op.drop_index("ix_integration_logs_provider", table_name="integration_logs")
    op.drop_index("ix_integration_logs_company_id", table_name="integration_logs")
    op.drop_table("integration_logs")

    op.drop_index("ix_integration_sync_jobs_provider", table_name="integration_sync_jobs")
    op.drop_index("ix_integration_sync_jobs_company_id", table_name="integration_sync_jobs")
    op.drop_table("integration_sync_jobs")

    op.drop_index("ix_integration_connections_provider", table_name="integration_connections")
    op.drop_index("ix_integration_connections_company_id", table_name="integration_connections")
    op.drop_table("integration_connections")
