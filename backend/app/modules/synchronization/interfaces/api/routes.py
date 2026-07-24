"""API routes for synchronization orchestration."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.synchronization.application.orchestrator import SynchronizationOrchestrator
from app.modules.synchronization.application.scheduler import SynchronizationScheduler
from app.modules.synchronization.domain.entities import TimeWindow
from app.modules.synchronization.domain.value_objects import JobPriority, SyncDomain
from app.modules.synchronization.infrastructure.container import get_orchestrator, get_scheduler
from app.modules.synchronization.infrastructure.repositories import CheckpointRepository, JobRepository
from app.modules.synchronization.interfaces.api.schemas import (
    BatchResponse,
    CheckpointResponse,
    ListCheckpointsResponse,
    ListJobsResponse,
    OrchestratorHealthResponse,
    ScheduleDomainSyncRequest,
    ScheduleFullSyncRequest,
    ScheduleIncrementalSyncRequest,
    ScheduleStatusResponse,
    SyncJobResponse,
    TimeWindowResponse,
)

router = APIRouter(prefix="/v1/synchronization", tags=["synchronization"])


@router.get("/health", response_model=OrchestratorHealthResponse)
def get_orchestrator_health(
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
) -> dict:
    """Get orchestrator health status."""
    return orchestrator.health()


@router.get("/scheduler/status", response_model=ScheduleStatusResponse)
def get_scheduler_status(
    scheduler: SynchronizationScheduler = Depends(get_scheduler),
) -> dict:
    """Get scheduler status."""
    return scheduler.get_schedule_status()


@router.post("/scheduler/start")
def start_scheduler(
    scheduler: SynchronizationScheduler = Depends(get_scheduler),
) -> dict:
    """Start the scheduler."""
    scheduler.start()
    return {"message": "Scheduler started"}


@router.post("/scheduler/stop")
def stop_scheduler(
    scheduler: SynchronizationScheduler = Depends(get_scheduler),
) -> dict:
    """Stop the scheduler."""
    scheduler.stop()
    return {"message": "Scheduler stopped"}


@router.get("/jobs", response_model=ListJobsResponse)
def list_jobs(
    company_id: str | None = None,
    provider: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_db),
) -> dict:
    """List synchronization jobs."""
    job_repository = JobRepository(session=session)
    jobs = job_repository.list_jobs(
        company_id=company_id,
        provider=provider,
        limit=limit,
    )

    return {
        "total": len(jobs),
        "jobs": [_job_to_response(job) for job in jobs],
    }


@router.get("/jobs/{job_id}", response_model=SyncJobResponse)
def get_job(
    job_id: str,
    session: Session = Depends(get_db),
) -> dict:
    """Get job details."""
    job_repository = JobRepository(session=session)
    job = job_repository.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return _job_to_response(job)


@router.post("/jobs/{job_id}/pause")
def pause_job(
    job_id: str,
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
) -> dict:
    """Pause a running job."""
    try:
        orchestrator.pause_job(job_id)
        return {"message": "Job paused"}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
) -> dict:
    """Cancel a job."""
    try:
        orchestrator.cancel_job(job_id)
        return {"message": "Job cancelled"}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/checkpoints", response_model=ListCheckpointsResponse)
def list_checkpoints(
    company_id: str,
    provider: str | None = None,
    domain: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_db),
) -> dict:
    """List checkpoints."""
    checkpoint_repository = CheckpointRepository(session=session)

    domain_enum = None
    if domain:
        try:
            domain_enum = SyncDomain(domain)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid domain: {domain}",
            )

    checkpoints = checkpoint_repository.list_checkpoints(
        company_id=company_id,
        provider=provider,
        domain=domain_enum,
        limit=limit,
    )

    return {
        "total": len(checkpoints),
        "checkpoints": [_checkpoint_to_response(cp) for cp in checkpoints],
    }


@router.get("/runtime")
def get_runtime_metrics(
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
) -> dict:
    """Get runtime metrics."""
    return orchestrator.runtime.health_snapshot()


def _job_to_response(job) -> dict:
    """Convert job entity to response dict."""
    window_resp = None
    if job.window:
        window_resp = TimeWindowResponse(
            window_id=job.window.window_id,
            start_date=job.window.start_date,
            end_date=job.window.end_date,
            days=job.window.days,
        ).model_dump()

    return SyncJobResponse(
        job_id=job.job_id,
        company_id=job.company_id,
        provider=job.provider,
        domain=job.domain.value,
        priority=job.priority.value,
        status=job.status.value,
        mode=job.mode,
        window=window_resp,
        checkpoint_id=job.checkpoint_id,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        records_read=job.records_read,
        records_imported=job.records_imported,
        records_failed=job.records_failed,
        pages_processed=job.pages_processed,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
        error_message=job.error_message,
        duration_seconds=job.duration_seconds,
        created_at=job.created_at,
        updated_at=job.updated_at,
    ).model_dump()


def _checkpoint_to_response(checkpoint) -> dict:
    """Convert checkpoint entity to response dict."""
    return CheckpointResponse(
        checkpoint_id=checkpoint.checkpoint_id,
        company_id=checkpoint.company_id,
        provider=checkpoint.provider,
        domain=checkpoint.domain.value,
        status=checkpoint.status.value,
        last_page=checkpoint.last_page,
        last_cursor=checkpoint.last_cursor,
        last_success_sync=checkpoint.last_success_sync,
        last_processed_record=checkpoint.last_processed_record,
        last_window_start=checkpoint.last_window_start,
        last_window_end=checkpoint.last_window_end,
        created_at=checkpoint.created_at,
        updated_at=checkpoint.updated_at,
    ).model_dump()
