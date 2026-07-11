from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class ExecutiveScoreModel(Base):
    __tablename__ = "executive_scores"

    executive_score_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    financial_score: Mapped[float] = mapped_column(Float, nullable=False)
    commercial_score: Mapped[float] = mapped_column(Float, nullable=False)
    operational_score: Mapped[float] = mapped_column(Float, nullable=False)
    inventory_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_version: Mapped[str] = mapped_column(String(32), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class KPIResultModel(Base):
    __tablename__ = "kpi_results"

    kpi_result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    period_grain: Mapped[str] = mapped_column(String(16), nullable=False, default="month")
    kpi_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    formula_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    kpi_name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend: Mapped[str | None] = mapped_column(String(32), nullable=True)
    health: Mapped[str | None] = mapped_column(String(16), nullable=True)
    orchestrator_run_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RuleEvaluationModel(Base):
    __tablename__ = "rule_evaluations"

    rule_evaluation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    potential_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InsightResultModel(Base):
    __tablename__ = "insight_results"

    insight_result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(32), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationResultModel(Base):
    __tablename__ = "recommendation_results"

    recommendation_result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    recommendation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rank_score: Mapped[float] = mapped_column(Float, nullable=False)
    expected_impact_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    owner_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sla_target: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TimelineSnapshotModel(Base):
    __tablename__ = "timeline_snapshots"

    timeline_snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    financial_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    commercial_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    operational_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_risks_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class SummaryProjectionModel(Base):
    __tablename__ = "executive_summary_projections"

    summary_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SummaryAuditLogModel(Base):
    __tablename__ = "executive_summary_audit_logs"

    audit_log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), nullable=False)
    summary_id: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


Index("ix_summary_projection_company_period", SummaryProjectionModel.company_id, SummaryProjectionModel.period_ref)
Index("ix_summary_audit_company_period", SummaryAuditLogModel.company_id, SummaryAuditLogModel.period_ref)
