from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.pipeline.application.contracts import StartPipelineCommand
from app.modules.pipeline.infrastructure.container import build_pipeline_container
from app.modules.pipeline.interfaces.api.schemas import (
    PipelineLogResponse,
    PipelineRunResponse,
    PipelineStepResponse,
    StartPipelineRequest,
)
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "pipeline", "status": "ok"}


@router.post("/internal/start", response_model=PipelineRunResponse)
def start_pipeline(payload: StartPipelineRequest, db: Session = Depends(get_db)) -> PipelineRunResponse:
    container = build_pipeline_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: container.service.start(
                StartPipelineCommand(
                    company_id=payload.company_id,
                    import_job_id=payload.import_job_id,
                    template=payload.template,
                    source_system=payload.source_system,
                    ingest_event_id=payload.ingest_event_id,
                    correlation_id=payload.correlation_id,
                    allow_retry=payload.allow_retry,
                )
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return PipelineRunResponse.model_validate(result, from_attributes=True)


@router.get("/{pipeline_run_id}", response_model=PipelineRunResponse)
def get_pipeline_run(pipeline_run_id: str, db: Session = Depends(get_db)) -> PipelineRunResponse:
    container = build_pipeline_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(lambda: container.service.get_run(pipeline_run_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PipelineRunResponse.model_validate(result, from_attributes=True)


@router.get("/{pipeline_run_id}/steps", response_model=list[PipelineStepResponse])
def get_pipeline_steps(pipeline_run_id: str, db: Session = Depends(get_db)) -> list[PipelineStepResponse]:
    container = build_pipeline_container(db)
    tx = TransactionBoundary(db)
    results = tx.execute(lambda: container.service.get_steps(pipeline_run_id))
    return [PipelineStepResponse.model_validate(item, from_attributes=True) for item in results]


@router.get("/{pipeline_run_id}/logs", response_model=list[PipelineLogResponse])
def get_pipeline_logs(pipeline_run_id: str, db: Session = Depends(get_db)) -> list[PipelineLogResponse]:
    container = build_pipeline_container(db)
    tx = TransactionBoundary(db)
    results = tx.execute(lambda: container.service.get_logs(pipeline_run_id))
    return [PipelineLogResponse.model_validate(item, from_attributes=True) for item in results]
