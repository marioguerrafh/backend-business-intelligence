from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"

    pipeline_run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    template: Mapped[str] = mapped_column(String(32), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_of_pipeline_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PipelineStepModel(Base):
    __tablename__ = "pipeline_steps"

    step_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    import_job_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PipelineLogModel(Base):
    __tablename__ = "pipeline_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    step_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class PipelineEventModel(Base):
    __tablename__ = "pipeline_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pipeline_run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_pipeline_runs_company_job", PipelineRunModel.company_id, PipelineRunModel.import_job_id)
Index("ix_pipeline_steps_run_order", PipelineStepModel.pipeline_run_id, PipelineStepModel.step_order)
Index("ix_pipeline_steps_company_job", PipelineStepModel.company_id, PipelineStepModel.import_job_id)
Index("ix_pipeline_logs_run", PipelineLogModel.pipeline_run_id)
Index("ix_pipeline_events_run", PipelineEventModel.pipeline_run_id)
