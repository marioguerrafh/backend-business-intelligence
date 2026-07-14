from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.modules.imports.infrastructure.models import ImportJobModel
from app.modules.pipeline.infrastructure.models import (
    PipelineEventModel,
    PipelineLogModel,
    PipelineRunModel,
    PipelineStepModel,
)
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class PipelineRepository:
    session: Session

    def create_or_reuse_run(
        self,
        *,
        company_id: str,
        import_job_id: str,
        template: str,
        source_system: str,
        correlation_id: str | None,
        allow_retry: bool,
    ) -> dict[str, object]:
        latest = self.latest_run_for_job(company_id=company_id, import_job_id=import_job_id)
        if latest is not None:
            if latest.status in {"PENDING", "RUNNING", "SUCCESS"}:
                return self._run_to_dict(latest, reused_existing_run=True)
            if latest.status == "FAILED" and not allow_retry:
                return self._run_to_dict(latest, reused_existing_run=True)

        retry_of = latest.pipeline_run_id if latest and latest.status == "FAILED" else None
        attempt = (latest.attempt + 1) if latest and latest.status == "FAILED" and allow_retry else 1

        run = PipelineRunModel(
            pipeline_run_id=f"plr_{uuid4().hex[:16]}",
            company_id=company_id,
            import_job_id=import_job_id,
            template=template,
            source_system=source_system,
            status="PENDING",
            progress=0,
            current_step=None,
            correlation_id=correlation_id,
            retry_of_pipeline_run_id=retry_of,
            attempt=attempt,
            started_at=datetime.now(timezone.utc),
            finished_at=None,
        )
        self.session.add(run)
        self.session.flush()
        return self._run_to_dict(run, reused_existing_run=False)

    def latest_run_for_job(self, *, company_id: str, import_job_id: str) -> PipelineRunModel | None:
        stmt = (
            select(PipelineRunModel)
            .where(
                PipelineRunModel.company_id == company_id,
                PipelineRunModel.import_job_id == import_job_id,
            )
            .order_by(desc(PipelineRunModel.started_at))
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def mark_run_running(self, *, pipeline_run_id: str) -> None:
        model = self._require_run(pipeline_run_id)
        model.status = "RUNNING"
        self.session.flush()

    def mark_run_failed(self, *, pipeline_run_id: str, current_step: str) -> None:
        model = self._require_run(pipeline_run_id)
        model.status = "FAILED"
        model.current_step = current_step
        model.finished_at = datetime.now(timezone.utc)
        model.progress = self._compute_progress(pipeline_run_id)
        self.session.flush()

    def mark_run_success(self, *, pipeline_run_id: str, current_step: str) -> None:
        model = self._require_run(pipeline_run_id)
        model.status = "SUCCESS"
        model.current_step = current_step
        model.progress = 100
        model.finished_at = datetime.now(timezone.utc)
        self.session.flush()

    def update_progress(self, *, pipeline_run_id: str, current_step: str) -> None:
        model = self._require_run(pipeline_run_id)
        model.current_step = current_step
        model.progress = self._compute_progress(pipeline_run_id)
        self.session.flush()

    def start_step(self, *, pipeline_run_id: str, company_id: str, step_name: str, step_order: int) -> str:
        run = self._require_run(pipeline_run_id)
        step = PipelineStepModel(
            step_id=f"pls_{uuid4().hex[:16]}",
            pipeline_run_id=pipeline_run_id,
            company_id=company_id,
            import_job_id=run.import_job_id,
            step_name=step_name,
            step_order=step_order,
            status="RUNNING",
            duration_ms=None,
            details_json=None,
            error_message=None,
            started_at=datetime.now(timezone.utc),
            finished_at=None,
        )
        self.session.add(step)
        self.session.flush()
        return step.step_id

    def finish_step(
        self,
        *,
        step_id: str,
        status: str,
        duration_ms: int,
        details_json: str | None,
        error_message: str | None,
    ) -> None:
        model = self.session.get(PipelineStepModel, step_id)
        if model is None:
            raise ValueError("pipeline step not found")
        model.status = status
        model.duration_ms = duration_ms
        model.details_json = details_json
        model.error_message = error_message
        model.finished_at = datetime.now(timezone.utc)
        self.session.flush()

    def was_step_successful_for_job(self, *, company_id: str, import_job_id: str, step_name: str) -> bool:
        stmt = (
            select(PipelineStepModel.step_id)
            .where(
                PipelineStepModel.company_id == company_id,
                PipelineStepModel.import_job_id == import_job_id,
                PipelineStepModel.step_name == step_name,
                PipelineStepModel.status == "SUCCESS",
            )
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def get_last_success_step_details(self, *, company_id: str, import_job_id: str, step_name: str) -> dict[str, object] | None:
        stmt = (
            select(PipelineStepModel)
            .where(
                PipelineStepModel.company_id == company_id,
                PipelineStepModel.import_job_id == import_job_id,
                PipelineStepModel.step_name == step_name,
                PipelineStepModel.status == "SUCCESS",
                PipelineStepModel.details_json.is_not(None),
            )
            .order_by(desc(PipelineStepModel.finished_at))
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None or not model.details_json:
            return None
        try:
            payload = json.loads(model.details_json)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def add_log(
        self,
        *,
        pipeline_run_id: str,
        company_id: str,
        step_name: str | None,
        status: str,
        message: str,
        duration_ms: int | None,
        correlation_id: str | None,
        error_message: str | None,
    ) -> None:
        self.session.add(
            PipelineLogModel(
                log_id=f"pll_{uuid4().hex[:16]}",
                pipeline_run_id=pipeline_run_id,
                company_id=company_id,
                step_name=step_name,
                status=status,
                duration_ms=duration_ms,
                message=message,
                error_message=error_message,
                correlation_id=correlation_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def publish_event(self, *, pipeline_run_id: str, company_id: str, topic: str, payload: dict[str, object]) -> str:
        event = IntegrationEvent(topic=topic, payload=payload)
        self.session.add(
            PipelineEventModel(
                event_id=event.event_id,
                pipeline_run_id=pipeline_run_id,
                company_id=company_id,
                topic=topic,
                payload_json=json.dumps(payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event.event_id

    def get_run(self, pipeline_run_id: str) -> dict[str, object] | None:
        model = self.session.get(PipelineRunModel, pipeline_run_id)
        if model is None:
            return None
        return self._run_to_dict(model)

    def list_steps(self, pipeline_run_id: str) -> list[dict[str, object]]:
        stmt = (
            select(PipelineStepModel)
            .where(PipelineStepModel.pipeline_run_id == pipeline_run_id)
            .order_by(PipelineStepModel.step_order.asc(), PipelineStepModel.started_at.asc())
        )
        return [self._step_to_dict(item) for item in self.session.execute(stmt).scalars().all()]

    def list_logs(self, pipeline_run_id: str) -> list[dict[str, object]]:
        stmt = (
            select(PipelineLogModel)
            .where(PipelineLogModel.pipeline_run_id == pipeline_run_id)
            .order_by(PipelineLogModel.created_at.asc())
        )
        rows = self.session.execute(stmt).scalars().all()
        result: list[dict[str, object]] = []
        for item in rows:
            result.append(
                {
                    "log_id": item.log_id,
                    "pipeline_run_id": item.pipeline_run_id,
                    "company_id": item.company_id,
                    "step_name": item.step_name,
                    "status": item.status,
                    "duration_ms": item.duration_ms,
                    "message": item.message,
                    "error_message": item.error_message,
                    "correlation_id": item.correlation_id,
                    "created_at": item.created_at,
                }
            )
        return result

    def get_import_job_progress(self, *, company_id: str, job_id: str) -> dict[str, object] | None:
        import_job = self.session.get(ImportJobModel, job_id)
        if import_job is None or import_job.company_id != company_id:
            return None

        run = self.latest_run_for_job(company_id=company_id, import_job_id=job_id)
        if run is None:
            # import finished but pipeline not started yet
            status = "processing" if import_job.status == "running" else "processing"
            return {
                "job_id": import_job.import_job_id,
                "status": status,
                "progress": 0,
                "current_step": None,
                "started_at": import_job.started_at,
                "estimated_remaining_seconds": 12,
                "summary_updated": False,
            }

        steps = self.list_steps(run.pipeline_run_id)
        completed_steps = [item for item in steps if item["status"] in {"SUCCESS", "SKIPPED"}]
        running_step = next((item for item in steps if item["status"] == "RUNNING"), None)

        total_steps = 6
        progress = int((len(completed_steps) / total_steps) * 100)
        if run.status == "SUCCESS":
            progress = 100

        avg_ms = 2000
        finished_with_duration = [item for item in steps if item["duration_ms"] and item["status"] in {"SUCCESS", "SKIPPED"}]
        if finished_with_duration:
            durations_ms = [
                duration
                for item in finished_with_duration
                for duration in [item["duration_ms"]]
                if isinstance(duration, int)
            ]
            if durations_ms:
                avg_ms = int(sum(durations_ms) / len(durations_ms))
        remaining = max(total_steps - len(completed_steps) - (1 if running_step else 0), 0)
        est_seconds = max(int((avg_ms * remaining) / 1000), 0)

        status_map = {
            "PENDING": "processing",
            "RUNNING": "processing",
            "SUCCESS": "completed",
            "FAILED": "failed",
        }

        summary_step = next(
            (item for item in steps if item["step_name"] == "Summary Engine" and item["status"] in {"SUCCESS", "SKIPPED"}),
            None,
        )

        return {
            "job_id": import_job.import_job_id,
            "status": status_map.get(run.status, "processing"),
            "progress": progress,
            "current_step": (running_step["step_name"] if running_step else run.current_step),
            "started_at": run.started_at,
            "estimated_remaining_seconds": 0 if run.status == "SUCCESS" else est_seconds,
            "summary_updated": summary_step is not None,
        }

    def _compute_progress(self, pipeline_run_id: str) -> int:
        total_stmt = select(func.count()).select_from(PipelineStepModel).where(
            PipelineStepModel.pipeline_run_id == pipeline_run_id
        )
        total = int(self.session.execute(total_stmt).scalar_one() or 0)
        if total == 0:
            return 0
        completed_stmt = select(func.count()).select_from(PipelineStepModel).where(
            and_(
                PipelineStepModel.pipeline_run_id == pipeline_run_id,
                PipelineStepModel.status.in_(["SUCCESS", "SKIPPED"]),
            )
        )
        completed = int(self.session.execute(completed_stmt).scalar_one() or 0)
        return int((completed / total) * 100)

    def _require_run(self, pipeline_run_id: str) -> PipelineRunModel:
        model = self.session.get(PipelineRunModel, pipeline_run_id)
        if model is None:
            raise ValueError("pipeline run not found")
        return model

    @staticmethod
    def _step_to_dict(item: PipelineStepModel) -> dict[str, object]:
        return {
            "step_id": item.step_id,
            "pipeline_run_id": item.pipeline_run_id,
            "step_name": item.step_name,
            "step_order": item.step_order,
            "status": item.status,
            "duration_ms": item.duration_ms,
            "started_at": item.started_at,
            "finished_at": item.finished_at,
            "error_message": item.error_message,
            "details_json": item.details_json,
        }

    @staticmethod
    def _run_to_dict(model: PipelineRunModel, *, reused_existing_run: bool = False) -> dict[str, object]:
        return {
            "pipeline_run_id": model.pipeline_run_id,
            "company_id": model.company_id,
            "import_job_id": model.import_job_id,
            "template": model.template,
            "status": model.status,
            "progress": model.progress,
            "current_step": model.current_step,
            "started_at": model.started_at,
            "finished_at": model.finished_at,
            "correlation_id": model.correlation_id,
            "retry_of_pipeline_run_id": model.retry_of_pipeline_run_id,
            "attempt": model.attempt,
            "reused_existing_run": reused_existing_run,
        }
