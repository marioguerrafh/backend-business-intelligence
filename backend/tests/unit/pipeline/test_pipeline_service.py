from __future__ import annotations

import json
from datetime import datetime, timezone

from app.modules.pipeline.application.contracts import StartPipelineCommand
from app.modules.pipeline.application.pipeline_service import PipelineService


class _FakeRepository:
    def __init__(self) -> None:
        self.run = {
            "pipeline_run_id": "plr_1",
            "company_id": "cmp_acme",
            "import_job_id": "imp_1",
            "template": "sales",
            "status": "PENDING",
            "progress": 0,
            "current_step": None,
            "started_at": datetime.now(timezone.utc),
            "finished_at": None,
            "correlation_id": "corr_1",
            "retry_of_pipeline_run_id": None,
            "attempt": 1,
            "reused_existing_run": False,
        }
        self.steps: list[dict[str, object]] = []
        self.logs: list[dict[str, object]] = []

    def create_or_reuse_run(self, **_: object) -> dict[str, object]:
        return dict(self.run)

    def mark_run_running(self, *, pipeline_run_id: str) -> None:
        assert pipeline_run_id == "plr_1"
        self.run["status"] = "RUNNING"

    def start_step(self, *, pipeline_run_id: str, company_id: str, step_name: str, step_order: int) -> str:
        step_id = f"step_{len(self.steps) + 1}"
        self.steps.append(
            {
                "step_id": step_id,
                "pipeline_run_id": pipeline_run_id,
                "company_id": company_id,
                "import_job_id": "imp_1",
                "step_name": step_name,
                "step_order": step_order,
                "status": "RUNNING",
                "duration_ms": None,
                "started_at": datetime.now(timezone.utc),
                "finished_at": None,
                "error_message": None,
                "details_json": None,
            }
        )
        return step_id

    def was_step_successful_for_job(self, **_: object) -> bool:
        return False

    def get_last_success_step_details(self, **_: object) -> dict[str, object] | None:
        return None

    def finish_step(self, *, step_id: str, status: str, duration_ms: int, details_json: str | None, error_message: str | None) -> None:
        step = next(item for item in self.steps if item["step_id"] == step_id)
        step["status"] = status
        step["duration_ms"] = duration_ms
        step["details_json"] = details_json
        step["error_message"] = error_message
        step["finished_at"] = datetime.now(timezone.utc)

    def add_log(self, **kwargs: object) -> None:
        self.logs.append(kwargs)

    def update_progress(self, *, pipeline_run_id: str, current_step: str) -> None:
        assert pipeline_run_id == "plr_1"
        self.run["current_step"] = current_step

    def mark_run_failed(self, *, pipeline_run_id: str, current_step: str) -> None:
        assert pipeline_run_id == "plr_1"
        self.run["status"] = "FAILED"
        self.run["current_step"] = current_step

    def mark_run_success(self, *, pipeline_run_id: str, current_step: str) -> None:
        assert pipeline_run_id == "plr_1"
        self.run["status"] = "SUCCESS"
        self.run["progress"] = 100
        self.run["current_step"] = current_step
        self.run["finished_at"] = datetime.now(timezone.utc)

    def get_run(self, pipeline_run_id: str) -> dict[str, object] | None:
        if pipeline_run_id != "plr_1":
            return None
        return dict(self.run)

    def list_steps(self, pipeline_run_id: str) -> list[dict[str, object]]:
        assert pipeline_run_id == "plr_1"
        return list(self.steps)

    def list_logs(self, pipeline_run_id: str) -> list[dict[str, object]]:
        assert pipeline_run_id == "plr_1"
        return [
            {
                "log_id": f"log_{idx}",
                "pipeline_run_id": "plr_1",
                "company_id": "cmp_acme",
                "step_name": item.get("step_name"),
                "status": item.get("status", "SUCCESS"),
                "duration_ms": item.get("duration_ms"),
                "message": item.get("message", "ok"),
                "error_message": item.get("error_message"),
                "correlation_id": "corr_1",
                "created_at": datetime.now(timezone.utc),
            }
            for idx, item in enumerate(self.logs, start=1)
        ]

    def get_import_job_progress(self, *, company_id: str, job_id: str) -> dict[str, object] | None:
        if company_id != "cmp_acme" or job_id != "imp_1":
            return None
        return {
            "job_id": "imp_1",
            "status": "completed",
            "progress": 100,
            "current_step": "Summary Engine",
            "started_at": self.run["started_at"],
            "estimated_remaining_seconds": 0,
            "summary_updated": True,
        }


class _FakeExecutor:
    def run_kpi_orchestrator(self, *, context, fallback_run_id: str):
        context.period_ref = "2026-07"
        context.orchestrator_run_id = f"{fallback_run_id}-p1"
        return {
            "period_ref": "2026-07",
            "orchestrator_run_id": f"{fallback_run_id}-p1",
            "periods": [
                {"period_ref": "2026-07", "orchestrator_run_id": f"{fallback_run_id}-p1"},
                {"period_ref": "2026-06", "orchestrator_run_id": f"{fallback_run_id}-p2"},
            ],
        }

    def run_rule_engine(self, *, context, period_ref: str, orchestrator_run_id: str):
        assert period_ref in {"2026-07", "2026-06"}
        assert orchestrator_run_id in {"plr_1-p1", "plr_1-p2"}
        return {"fired_rules": 0}

    def run_recommendation_engine(self, *, context, period_ref: str, orchestrator_run_id: str):
        assert period_ref in {"2026-07", "2026-06"}
        assert orchestrator_run_id in {"plr_1-p1", "plr_1-p2"}
        return {"generated_count": 0}

    def run_insight_engine(self, *, context, period_ref: str, orchestrator_run_id: str):
        assert period_ref in {"2026-07", "2026-06"}
        assert orchestrator_run_id in {"plr_1-p1", "plr_1-p2"}
        return {"generated_count": 0}

    def run_executive_score_engine(self, *, context, period_ref: str, orchestrator_run_id: str):
        assert period_ref in {"2026-07", "2026-06"}
        assert orchestrator_run_id in {"plr_1-p1", "plr_1-p2"}
        return {"executive_score": 0.0}

    def run_summary_engine(self, *, context, period_ref: str, orchestrator_run_id: str):
        assert orchestrator_run_id in {"plr_1-p1", "plr_1-p2"}
        return {"summary_updated": True, "period_ref": period_ref}


class _FakePublisher:
    def __init__(self) -> None:
        self.topics: list[str] = []

    def pipeline_started(self, **_: object) -> str:
        self.topics.append("pipeline.started.v1")
        return "evt_1"

    def step_started(self, **_: object) -> str:
        self.topics.append("pipeline.step.started.v1")
        return "evt_2"

    def step_completed(self, **_: object) -> str:
        self.topics.append("pipeline.step.completed.v1")
        return "evt_3"

    def pipeline_failed(self, **_: object) -> str:
        self.topics.append("pipeline.failed.v1")
        return "evt_4"

    def pipeline_completed(self, **_: object) -> str:
        self.topics.append("pipeline.completed.v1")
        return "evt_5"


def test_pipeline_service_executes_all_stages_and_completes() -> None:
    repository = _FakeRepository()
    service = PipelineService(
        repository=repository,
        executor=_FakeExecutor(),
        event_publisher=_FakePublisher(),
    )

    result = service.start(
        StartPipelineCommand(
            company_id="cmp_acme",
            import_job_id="imp_1",
            template="sales",
            source_system="csv_manual",
            ingest_event_id="evt_ing_1",
            correlation_id="corr_1",
        )
    )

    assert result.status == "SUCCESS"
    assert result.progress == 100
    assert result.current_step == "Summary Engine"

    assert len(repository.steps) == 6
    assert {item["status"] for item in repository.steps} == {"SUCCESS"}

    kpi_step = next(item for item in repository.steps if item["step_name"] == "KPI Orchestrator")
    assert kpi_step["details_json"] is not None
    kpi_details = json.loads(str(kpi_step["details_json"]))
    assert kpi_details["period_ref"] == "2026-07"
    assert len(kpi_details["periods"]) == 2

    summary_step = next(item for item in repository.steps if item["step_name"] == "Summary Engine")
    assert summary_step["details_json"] is not None
    summary_details = json.loads(str(summary_step["details_json"]))
    assert summary_details["total_periods"] == 2
    assert {item["period_ref"] for item in summary_details["periods"]} == {"2026-07", "2026-06"}
