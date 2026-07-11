from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class InsightAuditLogModel(Base):
    __tablename__ = "insight_audit_logs"

    audit_log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False)
    orchestrator_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class InsightPublishedEventModel(Base):
    __tablename__ = "insight_published_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_insight_audit_company_period", InsightAuditLogModel.company_id, InsightAuditLogModel.period_ref)
Index(
    "ix_insight_published_company_period",
    InsightPublishedEventModel.company_id,
    InsightPublishedEventModel.period_ref,
)
