from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class RuleResultModel(Base):
    __tablename__ = "rule_results"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "period_ref",
            "kpi_id",
            "rule_id",
            name="uq_rule_results_dedup",
        ),
    )

    rule_result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    kpi_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    alert_title: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_description: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orchestrator_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)


class RuleAuditLogModel(Base):
    __tablename__ = "rule_audit_logs"

    audit_log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    kpi_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    expression: Mapped[str] = mapped_column(Text, nullable=False)
    trace_json: Mapped[str] = mapped_column(Text, nullable=False)
    fired: Mapped[str] = mapped_column(String(5), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    orchestrator_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class RulePublishedEventModel(Base):
    __tablename__ = "rule_published_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    kpi_id: Mapped[str] = mapped_column(String(64), nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_rule_results_company_period", RuleResultModel.company_id, RuleResultModel.period_ref)
Index("ix_rule_audit_company_period", RuleAuditLogModel.company_id, RuleAuditLogModel.period_ref)
Index("ix_rule_published_company_period", RulePublishedEventModel.company_id, RulePublishedEventModel.period_ref)
