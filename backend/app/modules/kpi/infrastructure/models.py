from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class OrchestratorRunModel(Base):
    __tablename__ = "orchestrator_runs"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "period_ref",
            "orchestrator_run_id",
            name="uq_orchestrator_run_company_period_run",
        ),
    )

    orchestrator_run_pk: Mapped[str] = mapped_column(String(64), primary_key=True)
    orchestrator_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    pipeline_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class KPIOrchestratorAuditLogModel(Base):
    __tablename__ = "kpi_orchestrator_audit_logs"

    audit_log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    orchestrator_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    formula_id: Mapped[str] = mapped_column(String(128), nullable=False)
    kpi_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    execution_steps_json: Mapped[str] = mapped_column(Text, nullable=False)
    inputs_used_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class KPIPublishedEventModel(Base):
    __tablename__ = "kpi_published_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    orchestrator_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_orchestrator_runs_company_period", OrchestratorRunModel.company_id, OrchestratorRunModel.period_ref)
Index(
    "ix_orchestrator_audit_company_period",
    KPIOrchestratorAuditLogModel.company_id,
    KPIOrchestratorAuditLogModel.period_ref,
)
Index("ix_kpi_published_events_company_period", KPIPublishedEventModel.company_id, KPIPublishedEventModel.period_ref)
