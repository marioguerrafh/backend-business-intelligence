from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

from app.modules.pipeline.application.contracts import (
    ImportJobProgressResult,
    PipelineLogResult,
    PipelineRunResult,
    PipelineStepResult,
    StartPipelineCommand,
)
from app.modules.pipeline.application.pipeline_executor import PipelineExecutionContext
from app.modules.pipeline.domain.entities import PipelineStageName, PipelineStatus


@dataclass(slots=True)
class PipelineService:
    repository: object
    executor: object
    event_publisher: object

    STAGES: tuple[tuple[int, PipelineStageName], ...] = (
        (1, PipelineStageName.KPI_ORCHESTRATOR),
        (2, PipelineStageName.RULE_ENGINE),
        (3, PipelineStageName.RECOMMENDATION_ENGINE),
        (4, PipelineStageName.INSIGHT_ENGINE),
        (5, PipelineStageName.EXECUTIVE_SCORE_ENGINE),
        (6, PipelineStageName.SUMMARY_ENGINE),
    )

    def start(self, command: StartPipelineCommand) -> PipelineRunResult:
        run = self.repository.create_or_reuse_run(
            company_id=command.company_id,
            import_job_id=command.import_job_id,
            template=command.template,
            source_system=command.source_system,
            correlation_id=command.correlation_id,
            allow_retry=command.allow_retry,
        )

        if run.get("reused_existing_run"):
            return self._run_result(run)

        self.repository.mark_run_running(pipeline_run_id=run["pipeline_run_id"])
        self.event_publisher.pipeline_started(
            pipeline_run_id=run["pipeline_run_id"],
            company_id=run["company_id"],
            payload={
                "company_id": run["company_id"],
                "pipeline_run_id": run["pipeline_run_id"],
                "import_job_id": run["import_job_id"],
                "template": run["template"],
                "attempt": run["attempt"],
                "status": "RUNNING",
            },
        )

        context = PipelineExecutionContext(
            company_id=command.company_id,
            import_job_id=command.import_job_id,
            template=command.template,
            source_system=command.source_system,
            ingest_event_id=command.ingest_event_id,
            correlation_id=command.correlation_id,
        )

        for order, stage_name in self.STAGES:
            step_start = perf_counter()
            step_id = self.repository.start_step(
                pipeline_run_id=run["pipeline_run_id"],
                company_id=run["company_id"],
                step_name=stage_name.value,
                step_order=order,
            )
            self.event_publisher.step_started(
                pipeline_run_id=run["pipeline_run_id"],
                company_id=run["company_id"],
                payload={
                    "company_id": run["company_id"],
                    "pipeline_run_id": run["pipeline_run_id"],
                    "step": stage_name.value,
                    "status": "RUNNING",
                },
            )

            # Skip step if same import job already completed successfully in a previous run.
            if self.repository.was_step_successful_for_job(
                company_id=run["company_id"],
                import_job_id=run["import_job_id"],
                step_name=stage_name.value,
            ):
                self._hydrate_context_from_previous_success(
                    company_id=run["company_id"],
                    import_job_id=run["import_job_id"],
                    step_name=stage_name.value,
                    context=context,
                )
                duration_ms = int((perf_counter() - step_start) * 1000)
                self.repository.finish_step(
                    step_id=step_id,
                    status=PipelineStatus.SKIPPED.value,
                    duration_ms=duration_ms,
                    details_json=json.dumps({"reason": "idempotent_success"}),
                    error_message=None,
                )
                self.repository.add_log(
                    pipeline_run_id=run["pipeline_run_id"],
                    company_id=run["company_id"],
                    step_name=stage_name.value,
                    status=PipelineStatus.SKIPPED.value,
                    message="step skipped due to previous successful execution",
                    duration_ms=duration_ms,
                    correlation_id=run.get("correlation_id"),
                    error_message=None,
                )
                self.event_publisher.step_completed(
                    pipeline_run_id=run["pipeline_run_id"],
                    company_id=run["company_id"],
                    payload={
                        "company_id": run["company_id"],
                        "pipeline_run_id": run["pipeline_run_id"],
                        "step": stage_name.value,
                        "status": PipelineStatus.SKIPPED.value,
                        "duration_ms": duration_ms,
                    },
                )
                self.repository.update_progress(
                    pipeline_run_id=run["pipeline_run_id"],
                    current_step=stage_name.value,
                )
                continue

            try:
                details = self._execute_stage(
                    stage_name=stage_name,
                    context=context,
                    fallback_run_id=run["pipeline_run_id"],
                )
                duration_ms = int((perf_counter() - step_start) * 1000)
                self.repository.finish_step(
                    step_id=step_id,
                    status=PipelineStatus.SUCCESS.value,
                    duration_ms=duration_ms,
                    details_json=json.dumps(details),
                    error_message=None,
                )
                self.repository.add_log(
                    pipeline_run_id=run["pipeline_run_id"],
                    company_id=run["company_id"],
                    step_name=stage_name.value,
                    status=PipelineStatus.SUCCESS.value,
                    message="step executed successfully",
                    duration_ms=duration_ms,
                    correlation_id=run.get("correlation_id"),
                    error_message=None,
                )
                self.event_publisher.step_completed(
                    pipeline_run_id=run["pipeline_run_id"],
                    company_id=run["company_id"],
                    payload={
                        "company_id": run["company_id"],
                        "pipeline_run_id": run["pipeline_run_id"],
                        "step": stage_name.value,
                        "status": PipelineStatus.SUCCESS.value,
                        "duration_ms": duration_ms,
                    },
                )
                self.repository.update_progress(
                    pipeline_run_id=run["pipeline_run_id"],
                    current_step=stage_name.value,
                )
            except Exception as exc:
                duration_ms = int((perf_counter() - step_start) * 1000)
                error_message = str(exc)
                self.repository.finish_step(
                    step_id=step_id,
                    status=PipelineStatus.FAILED.value,
                    duration_ms=duration_ms,
                    details_json=None,
                    error_message=error_message,
                )
                self.repository.add_log(
                    pipeline_run_id=run["pipeline_run_id"],
                    company_id=run["company_id"],
                    step_name=stage_name.value,
                    status=PipelineStatus.FAILED.value,
                    message="step execution failed",
                    duration_ms=duration_ms,
                    correlation_id=run.get("correlation_id"),
                    error_message=error_message,
                )
                self.repository.mark_run_failed(
                    pipeline_run_id=run["pipeline_run_id"],
                    current_step=stage_name.value,
                )
                self.event_publisher.pipeline_failed(
                    pipeline_run_id=run["pipeline_run_id"],
                    company_id=run["company_id"],
                    payload={
                        "company_id": run["company_id"],
                        "pipeline_run_id": run["pipeline_run_id"],
                        "step": stage_name.value,
                        "status": PipelineStatus.FAILED.value,
                        "error_message": error_message,
                        "duration_ms": duration_ms,
                    },
                )
                return self._run_result(self.repository.get_run(run["pipeline_run_id"]))

        self.repository.mark_run_success(
            pipeline_run_id=run["pipeline_run_id"],
            current_step=PipelineStageName.SUMMARY_ENGINE.value,
        )
        self.event_publisher.pipeline_completed(
            pipeline_run_id=run["pipeline_run_id"],
            company_id=run["company_id"],
            payload={
                "company_id": run["company_id"],
                "pipeline_run_id": run["pipeline_run_id"],
                "status": PipelineStatus.SUCCESS.value,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "summary_updated": True,
            },
        )
        return self._run_result(self.repository.get_run(run["pipeline_run_id"]))

    def get_run(self, pipeline_run_id: str) -> PipelineRunResult:
        run = self.repository.get_run(pipeline_run_id)
        if run is None:
            raise ValueError("pipeline run not found")
        return self._run_result(run)

    def get_steps(self, pipeline_run_id: str) -> list[PipelineStepResult]:
        return [
            PipelineStepResult(
                step_id=item["step_id"],
                pipeline_run_id=item["pipeline_run_id"],
                step_name=item["step_name"],
                step_order=item["step_order"],
                status=item["status"],
                duration_ms=item["duration_ms"],
                started_at=item["started_at"],
                finished_at=item["finished_at"],
                error_message=item["error_message"],
            )
            for item in self.repository.list_steps(pipeline_run_id)
        ]

    def get_logs(self, pipeline_run_id: str) -> list[PipelineLogResult]:
        return [
            PipelineLogResult(
                log_id=item["log_id"],
                pipeline_run_id=item["pipeline_run_id"],
                company_id=item["company_id"],
                step_name=item["step_name"],
                status=item["status"],
                duration_ms=item["duration_ms"],
                message=item["message"],
                error_message=item["error_message"],
                correlation_id=item["correlation_id"],
                created_at=item["created_at"],
            )
            for item in self.repository.list_logs(pipeline_run_id)
        ]

    def get_import_job_progress(self, *, company_id: str, job_id: str) -> ImportJobProgressResult:
        snapshot = self.repository.get_import_job_progress(company_id=company_id, job_id=job_id)
        if snapshot is None:
            raise ValueError("import job not found")

        return ImportJobProgressResult(
            job_id=snapshot["job_id"],
            status=snapshot["status"],
            progress=snapshot["progress"],
            current_step=snapshot["current_step"],
            started_at=snapshot["started_at"],
            estimated_remaining_seconds=snapshot["estimated_remaining_seconds"],
            summary_updated=snapshot["summary_updated"],
        )

    def _execute_stage(
        self,
        *,
        stage_name: PipelineStageName,
        context: PipelineExecutionContext,
        fallback_run_id: str,
    ) -> dict[str, object]:
        if stage_name is PipelineStageName.KPI_ORCHESTRATOR:
            return self.executor.run_kpi_orchestrator(context=context, fallback_run_id=fallback_run_id)
        if stage_name is PipelineStageName.RULE_ENGINE:
            return self.executor.run_rule_engine(context=context)
        if stage_name is PipelineStageName.RECOMMENDATION_ENGINE:
            return self.executor.run_recommendation_engine(context=context)
        if stage_name is PipelineStageName.INSIGHT_ENGINE:
            return self.executor.run_insight_engine(context=context)
        if stage_name is PipelineStageName.EXECUTIVE_SCORE_ENGINE:
            return self.executor.run_executive_score_engine(context=context)
        return self.executor.run_summary_engine(context=context)

    def _hydrate_context_from_previous_success(
        self,
        *,
        company_id: str,
        import_job_id: str,
        step_name: str,
        context: PipelineExecutionContext,
    ) -> None:
        details = self.repository.get_last_success_step_details(
            company_id=company_id,
            import_job_id=import_job_id,
            step_name=step_name,
        )
        if not details:
            return

        if step_name == PipelineStageName.KPI_ORCHESTRATOR.value:
            period_ref = details.get("period_ref")
            orchestrator_run_id = details.get("orchestrator_run_id")
            if isinstance(period_ref, str) and period_ref:
                context.period_ref = period_ref
            if isinstance(orchestrator_run_id, str) and orchestrator_run_id:
                context.orchestrator_run_id = orchestrator_run_id

    @staticmethod
    def _run_result(run: dict[str, object]) -> PipelineRunResult:
        return PipelineRunResult(
            pipeline_run_id=run["pipeline_run_id"],
            company_id=run["company_id"],
            import_job_id=run["import_job_id"],
            template=run["template"],
            status=run["status"],
            progress=run["progress"],
            current_step=run["current_step"],
            started_at=run["started_at"],
            finished_at=run["finished_at"],
            correlation_id=run.get("correlation_id"),
            reused_existing_run=bool(run.get("reused_existing_run", False)),
            retry_of_pipeline_run_id=run.get("retry_of_pipeline_run_id"),
            attempt=int(run.get("attempt", 1)),
        )
