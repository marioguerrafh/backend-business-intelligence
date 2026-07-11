"""recommendation insight executive schema

Revision ID: 20260711_0006
Revises: 20260711_0005
Create Date: 2026-07-11 02:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260711_0006"
down_revision = "20260711_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("executive_scores", sa.Column("inventory_score", sa.Float(), nullable=True))

    op.create_unique_constraint(
        "uq_recommendation_results_company_period_rec",
        "recommendation_results",
        ["company_id", "period_ref", "recommendation_id"],
    )

    op.create_table(
        "recommendation_audit_logs",
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("recommendation_id", sa.String(length=64), nullable=False),
        sa.Column("trigger_rule_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index("ix_recommendation_audit_logs_company_id", "recommendation_audit_logs", ["company_id"])
    op.create_index("ix_recommendation_audit_logs_period_ref", "recommendation_audit_logs", ["period_ref"])
    op.create_index(
        "ix_recommendation_audit_logs_recommendation_id",
        "recommendation_audit_logs",
        ["recommendation_id"],
    )
    op.create_index(
        "ix_recommendation_audit_logs_trigger_rule_id",
        "recommendation_audit_logs",
        ["trigger_rule_id"],
    )
    op.create_index(
        "ix_recommendation_audit_logs_orchestrator_run_id",
        "recommendation_audit_logs",
        ["orchestrator_run_id"],
    )
    op.create_index(
        "ix_recommendation_audit_company_period",
        "recommendation_audit_logs",
        ["company_id", "period_ref"],
    )

    op.create_table(
        "recommendation_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("recommendation_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_recommendation_published_events_company_id",
        "recommendation_published_events",
        ["company_id"],
    )
    op.create_index(
        "ix_recommendation_published_events_period_ref",
        "recommendation_published_events",
        ["period_ref"],
    )
    op.create_index(
        "ix_recommendation_published_events_recommendation_id",
        "recommendation_published_events",
        ["recommendation_id"],
    )
    op.create_index(
        "ix_recommendation_published_company_period",
        "recommendation_published_events",
        ["company_id", "period_ref"],
    )

    op.create_table(
        "insight_audit_logs",
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("insight_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index("ix_insight_audit_logs_company_id", "insight_audit_logs", ["company_id"])
    op.create_index("ix_insight_audit_logs_period_ref", "insight_audit_logs", ["period_ref"])
    op.create_index("ix_insight_audit_logs_insight_type", "insight_audit_logs", ["insight_type"])
    op.create_index(
        "ix_insight_audit_logs_orchestrator_run_id",
        "insight_audit_logs",
        ["orchestrator_run_id"],
    )
    op.create_index("ix_insight_audit_company_period", "insight_audit_logs", ["company_id", "period_ref"])

    op.create_table(
        "insight_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("insight_type", sa.String(length=32), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_insight_published_events_company_id", "insight_published_events", ["company_id"])
    op.create_index("ix_insight_published_events_period_ref", "insight_published_events", ["period_ref"])
    op.create_index("ix_insight_published_events_insight_type", "insight_published_events", ["insight_type"])
    op.create_index(
        "ix_insight_published_company_period",
        "insight_published_events",
        ["company_id", "period_ref"],
    )

    op.create_table(
        "executive_score_audit_logs",
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("orchestrator_run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index(
        "ix_executive_score_audit_logs_company_id",
        "executive_score_audit_logs",
        ["company_id"],
    )
    op.create_index(
        "ix_executive_score_audit_logs_period_ref",
        "executive_score_audit_logs",
        ["period_ref"],
    )
    op.create_index(
        "ix_executive_score_audit_logs_orchestrator_run_id",
        "executive_score_audit_logs",
        ["orchestrator_run_id"],
    )
    op.create_index(
        "ix_executive_score_audit_company_period",
        "executive_score_audit_logs",
        ["company_id", "period_ref"],
    )

    op.create_table(
        "executive_score_published_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_executive_score_published_events_company_id",
        "executive_score_published_events",
        ["company_id"],
    )
    op.create_index(
        "ix_executive_score_published_events_period_ref",
        "executive_score_published_events",
        ["period_ref"],
    )
    op.create_index(
        "ix_executive_score_published_company_period",
        "executive_score_published_events",
        ["company_id", "period_ref"],
    )


def downgrade() -> None:
    op.drop_index("ix_executive_score_published_company_period", table_name="executive_score_published_events")
    op.drop_index("ix_executive_score_published_events_period_ref", table_name="executive_score_published_events")
    op.drop_index("ix_executive_score_published_events_company_id", table_name="executive_score_published_events")
    op.drop_table("executive_score_published_events")

    op.drop_index("ix_executive_score_audit_company_period", table_name="executive_score_audit_logs")
    op.drop_index("ix_executive_score_audit_logs_orchestrator_run_id", table_name="executive_score_audit_logs")
    op.drop_index("ix_executive_score_audit_logs_period_ref", table_name="executive_score_audit_logs")
    op.drop_index("ix_executive_score_audit_logs_company_id", table_name="executive_score_audit_logs")
    op.drop_table("executive_score_audit_logs")

    op.drop_index("ix_insight_published_company_period", table_name="insight_published_events")
    op.drop_index("ix_insight_published_events_insight_type", table_name="insight_published_events")
    op.drop_index("ix_insight_published_events_period_ref", table_name="insight_published_events")
    op.drop_index("ix_insight_published_events_company_id", table_name="insight_published_events")
    op.drop_table("insight_published_events")

    op.drop_index("ix_insight_audit_company_period", table_name="insight_audit_logs")
    op.drop_index("ix_insight_audit_logs_orchestrator_run_id", table_name="insight_audit_logs")
    op.drop_index("ix_insight_audit_logs_insight_type", table_name="insight_audit_logs")
    op.drop_index("ix_insight_audit_logs_period_ref", table_name="insight_audit_logs")
    op.drop_index("ix_insight_audit_logs_company_id", table_name="insight_audit_logs")
    op.drop_table("insight_audit_logs")

    op.drop_index("ix_recommendation_published_company_period", table_name="recommendation_published_events")
    op.drop_index("ix_recommendation_published_events_recommendation_id", table_name="recommendation_published_events")
    op.drop_index("ix_recommendation_published_events_period_ref", table_name="recommendation_published_events")
    op.drop_index("ix_recommendation_published_events_company_id", table_name="recommendation_published_events")
    op.drop_table("recommendation_published_events")

    op.drop_index("ix_recommendation_audit_company_period", table_name="recommendation_audit_logs")
    op.drop_index("ix_recommendation_audit_logs_orchestrator_run_id", table_name="recommendation_audit_logs")
    op.drop_index("ix_recommendation_audit_logs_trigger_rule_id", table_name="recommendation_audit_logs")
    op.drop_index("ix_recommendation_audit_logs_recommendation_id", table_name="recommendation_audit_logs")
    op.drop_index("ix_recommendation_audit_logs_period_ref", table_name="recommendation_audit_logs")
    op.drop_index("ix_recommendation_audit_logs_company_id", table_name="recommendation_audit_logs")
    op.drop_table("recommendation_audit_logs")

    op.drop_constraint("uq_recommendation_results_company_period_rec", "recommendation_results", type_="unique")
    op.drop_column("executive_scores", "inventory_score")
