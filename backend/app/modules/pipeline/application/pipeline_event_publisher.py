from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PipelineEventPublisher:
    repository: object

    def pipeline_started(self, *, pipeline_run_id: str, company_id: str, payload: dict[str, object]) -> str:
        return self.repository.publish_event(
            pipeline_run_id=pipeline_run_id,
            company_id=company_id,
            topic="pipeline.started.v1",
            payload=payload,
        )

    def step_started(self, *, pipeline_run_id: str, company_id: str, payload: dict[str, object]) -> str:
        return self.repository.publish_event(
            pipeline_run_id=pipeline_run_id,
            company_id=company_id,
            topic="pipeline.step.started.v1",
            payload=payload,
        )

    def step_completed(self, *, pipeline_run_id: str, company_id: str, payload: dict[str, object]) -> str:
        return self.repository.publish_event(
            pipeline_run_id=pipeline_run_id,
            company_id=company_id,
            topic="pipeline.step.completed.v1",
            payload=payload,
        )

    def pipeline_failed(self, *, pipeline_run_id: str, company_id: str, payload: dict[str, object]) -> str:
        return self.repository.publish_event(
            pipeline_run_id=pipeline_run_id,
            company_id=company_id,
            topic="pipeline.failed.v1",
            payload=payload,
        )

    def pipeline_completed(self, *, pipeline_run_id: str, company_id: str, payload: dict[str, object]) -> str:
        return self.repository.publish_event(
            pipeline_run_id=pipeline_run_id,
            company_id=company_id,
            topic="pipeline.completed.v1",
            payload=payload,
        )
