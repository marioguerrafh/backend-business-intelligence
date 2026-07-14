from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.modules.integrations.infrastructure.models import (
    IntegrationConnectionModel,
    IntegrationLogModel,
    IntegrationPublishedEventModel,
    IntegrationSyncJobModel,
)
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class IntegrationRepository:
    session: Session

    def create_connection(
        self,
        *,
        company_id: str,
        provider: str,
        encrypted_credentials: str,
    ) -> IntegrationConnectionModel:
        model = IntegrationConnectionModel(
            id=f"itc_{uuid4().hex[:16]}",
            company_id=company_id,
            provider=provider,
            credentials=encrypted_credentials,
            status="connected",
            enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(model)
        self.session.flush()
        return model

    def list_connections(self, *, company_id: str) -> list[IntegrationConnectionModel]:
        stmt = (
            select(IntegrationConnectionModel)
            .where(IntegrationConnectionModel.company_id == company_id)
            .order_by(IntegrationConnectionModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_connection(self, *, company_id: str, connection_id: str) -> IntegrationConnectionModel | None:
        stmt = select(IntegrationConnectionModel).where(
            IntegrationConnectionModel.company_id == company_id,
            IntegrationConnectionModel.id == connection_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def mark_disconnected(self, *, company_id: str, connection_id: str) -> None:
        model = self.get_connection(company_id=company_id, connection_id=connection_id)
        if model is None:
            raise ValueError("integration connection not found")
        model.enabled = False
        model.status = "disconnected"
        model.updated_at = datetime.now(timezone.utc)
        self.session.flush()

    def mark_sync_success(self, *, company_id: str, connection_id: str) -> None:
        model = self.get_connection(company_id=company_id, connection_id=connection_id)
        if model is None:
            raise ValueError("integration connection not found")
        now = datetime.now(timezone.utc)
        model.last_sync = now
        model.last_success_sync = now
        model.status = "connected"
        model.updated_at = now
        self.session.flush()

    def mark_sync_failed(self, *, company_id: str, connection_id: str) -> None:
        model = self.get_connection(company_id=company_id, connection_id=connection_id)
        if model is None:
            raise ValueError("integration connection not found")
        model.last_sync = datetime.now(timezone.utc)
        model.status = "error"
        model.updated_at = datetime.now(timezone.utc)
        self.session.flush()

    def create_sync_job(self, *, provider: str, company_id: str) -> IntegrationSyncJobModel:
        model = IntegrationSyncJobModel(
            job_id=f"isj_{uuid4().hex[:16]}",
            provider=provider,
            company_id=company_id,
            status="running",
            started_at=datetime.now(timezone.utc),
            finished_at=None,
            duration_ms=None,
            records_read=0,
            records_imported=0,
            records_failed=0,
            pipeline_run_id=None,
        )
        self.session.add(model)
        self.session.flush()
        return model

    def complete_sync_job(
        self,
        *,
        job_id: str,
        status: str,
        records_read: int,
        records_imported: int,
        records_failed: int,
        pipeline_run_id: str | None,
    ) -> IntegrationSyncJobModel:
        model = self.session.get(IntegrationSyncJobModel, job_id)
        if model is None:
            raise ValueError("integration sync job not found")
        model.status = status
        model.records_read = records_read
        model.records_imported = records_imported
        model.records_failed = records_failed
        model.pipeline_run_id = pipeline_run_id
        model.finished_at = datetime.now(timezone.utc)
        model.duration_ms = int((model.finished_at - model.started_at).total_seconds() * 1000)
        self.session.flush()
        return model

    def list_jobs(self, *, company_id: str) -> list[IntegrationSyncJobModel]:
        stmt = (
            select(IntegrationSyncJobModel)
            .where(IntegrationSyncJobModel.company_id == company_id)
            .order_by(desc(IntegrationSyncJobModel.started_at))
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_job(self, *, company_id: str, job_id: str) -> IntegrationSyncJobModel | None:
        stmt = select(IntegrationSyncJobModel).where(
            IntegrationSyncJobModel.company_id == company_id,
            IntegrationSyncJobModel.job_id == job_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def add_log(
        self,
        *,
        company_id: str,
        provider: str,
        endpoint: str,
        request_payload: dict[str, object],
        duration_ms: int,
        status: str,
        error_message: str | None,
    ) -> None:
        self.session.add(
            IntegrationLogModel(
                log_id=f"ilg_{uuid4().hex[:16]}",
                company_id=company_id,
                provider=provider,
                endpoint=endpoint,
                request_json=json.dumps(request_payload),
                duration_ms=duration_ms,
                status=status,
                error_message=error_message,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_event(self, *, provider: str, company_id: str, topic: str, payload: dict[str, object]) -> str:
        event = IntegrationEvent(topic=topic, payload=payload)
        self.session.add(
            IntegrationPublishedEventModel(
                event_id=event.event_id,
                provider=provider,
                company_id=company_id,
                topic=topic,
                payload_json=json.dumps(payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id
