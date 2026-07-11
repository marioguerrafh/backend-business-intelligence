"""summary engine schema

Revision ID: 20260710_0002
Revises: 20260710_0001
Create Date: 2026-07-10 01:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260710_0002"
down_revision = "20260710_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "executive_scores",
        sa.Column("executive_score_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("financial_score", sa.Float(), nullable=False),
        sa.Column("commercial_score", sa.Float(), nullable=False),
        sa.Column("operational_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("score_version", sa.String(length=32), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("executive_score_id"),
    )
    op.create_index("ix_executive_scores_company_id", "executive_scores", ["company_id"])
    op.create_index("ix_executive_scores_period_ref", "executive_scores", ["period_ref"])

    op.create_table(
        "kpi_results",
        sa.Column("kpi_result_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("kpi_id", sa.String(length=64), nullable=False),
        sa.Column("kpi_name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("trend", sa.String(length=32), nullable=True),
        sa.Column("health", sa.String(length=16), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("kpi_result_id"),
    )
    op.create_index("ix_kpi_results_company_id", "kpi_results", ["company_id"])
    op.create_index("ix_kpi_results_period_ref", "kpi_results", ["period_ref"])
    op.create_index("ix_kpi_results_kpi_id", "kpi_results", ["kpi_id"])

    op.create_table(
        "rule_evaluations",
        sa.Column("rule_evaluation_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.String(length=8), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_code", sa.String(length=64), nullable=True),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("potential_impact", sa.Float(), nullable=True),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("rule_evaluation_id"),
    )
    op.create_index("ix_rule_evaluations_company_id", "rule_evaluations", ["company_id"])
    op.create_index("ix_rule_evaluations_period_ref", "rule_evaluations", ["period_ref"])

    op.create_table(
        "insight_results",
        sa.Column("insight_result_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("insight_type", sa.String(length=32), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("insight_result_id"),
    )
    op.create_index("ix_insight_results_company_id", "insight_results", ["company_id"])
    op.create_index("ix_insight_results_period_ref", "insight_results", ["period_ref"])

    op.create_table(
        "recommendation_results",
        sa.Column("recommendation_result_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("recommendation_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rank_score", sa.Float(), nullable=False),
        sa.Column("expected_impact_json", sa.JSON(), nullable=False),
        sa.Column("owner_role", sa.String(length=64), nullable=True),
        sa.Column("sla_target", sa.String(length=64), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("recommendation_result_id"),
    )
    op.create_index("ix_recommendation_results_company_id", "recommendation_results", ["company_id"])
    op.create_index("ix_recommendation_results_period_ref", "recommendation_results", ["period_ref"])

    op.create_table(
        "timeline_snapshots",
        sa.Column("timeline_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("financial_score", sa.Float(), nullable=True),
        sa.Column("commercial_score", sa.Float(), nullable=True),
        sa.Column("operational_score", sa.Float(), nullable=True),
        sa.Column("top_risks_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("timeline_snapshot_id"),
    )
    op.create_index("ix_timeline_snapshots_company_id", "timeline_snapshots", ["company_id"])
    op.create_index("ix_timeline_snapshots_snapshot_date", "timeline_snapshots", ["snapshot_date"])

    op.create_table(
        "executive_summary_projections",
        sa.Column("summary_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("summary_id"),
    )
    op.create_index("ix_executive_summary_projections_company_id", "executive_summary_projections", ["company_id"])
    op.create_index("ix_executive_summary_projections_period_ref", "executive_summary_projections", ["period_ref"])
    op.create_index(
        "ix_summary_projection_company_period",
        "executive_summary_projections",
        ["company_id", "period_ref"],
    )

    op.create_table(
        "executive_summary_audit_logs",
        sa.Column("audit_log_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("period_ref", sa.String(length=32), nullable=False),
        sa.Column("summary_id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_log_id"),
    )
    op.create_index("ix_executive_summary_audit_logs_company_id", "executive_summary_audit_logs", ["company_id"])
    op.create_index(
        "ix_summary_audit_company_period",
        "executive_summary_audit_logs",
        ["company_id", "period_ref"],
    )


def downgrade() -> None:
    op.drop_index("ix_summary_audit_company_period", table_name="executive_summary_audit_logs")
    op.drop_index("ix_executive_summary_audit_logs_company_id", table_name="executive_summary_audit_logs")
    op.drop_table("executive_summary_audit_logs")

    op.drop_index("ix_summary_projection_company_period", table_name="executive_summary_projections")
    op.drop_index("ix_executive_summary_projections_period_ref", table_name="executive_summary_projections")
    op.drop_index("ix_executive_summary_projections_company_id", table_name="executive_summary_projections")
    op.drop_table("executive_summary_projections")

    op.drop_index("ix_timeline_snapshots_snapshot_date", table_name="timeline_snapshots")
    op.drop_index("ix_timeline_snapshots_company_id", table_name="timeline_snapshots")
    op.drop_table("timeline_snapshots")

    op.drop_index("ix_recommendation_results_period_ref", table_name="recommendation_results")
    op.drop_index("ix_recommendation_results_company_id", table_name="recommendation_results")
    op.drop_table("recommendation_results")

    op.drop_index("ix_insight_results_period_ref", table_name="insight_results")
    op.drop_index("ix_insight_results_company_id", table_name="insight_results")
    op.drop_table("insight_results")

    op.drop_index("ix_rule_evaluations_period_ref", table_name="rule_evaluations")
    op.drop_index("ix_rule_evaluations_company_id", table_name="rule_evaluations")
    op.drop_table("rule_evaluations")

    op.drop_index("ix_kpi_results_kpi_id", table_name="kpi_results")
    op.drop_index("ix_kpi_results_period_ref", table_name="kpi_results")
    op.drop_index("ix_kpi_results_company_id", table_name="kpi_results")
    op.drop_table("kpi_results")

    op.drop_index("ix_executive_scores_period_ref", table_name="executive_scores")
    op.drop_index("ix_executive_scores_company_id", table_name="executive_scores")
    op.drop_table("executive_scores")
