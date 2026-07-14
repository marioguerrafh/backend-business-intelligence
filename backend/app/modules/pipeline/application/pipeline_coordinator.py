from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.modules.imports.application.contracts import ImportTemplate
from app.modules.pipeline.application.contracts import PipelineRunResult, StartPipelineCommand


class PipelineStarter(Protocol):
    def start(self, command: StartPipelineCommand) -> PipelineRunResult: ...


@dataclass(slots=True)
class PipelineCoordinator:
    service: PipelineStarter

    def consume_ingest_completed(
        self,
        *,
        company_id: str,
        import_job_id: str,
        template: ImportTemplate,
        source_system: str,
        event_id: str | None,
        correlation_id: str | None,
    ) -> PipelineRunResult:
        return self.service.start(
            StartPipelineCommand(
                company_id=company_id,
                import_job_id=import_job_id,
                template=template,
                source_system=source_system,
                ingest_event_id=event_id,
                correlation_id=correlation_id,
                allow_retry=False,
            )
        )
