"""API routes for synchronization orchestration."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
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

router = APIRouter(prefix="/synchronization", tags=["synchronization"])


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


@router.post("/schedule/full")
def schedule_full_sync(
    request: ScheduleFullSyncRequest,
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
    session: Session = Depends(get_db),
) -> dict:
    """Schedule full synchronization for multiple domains."""
    try:
        domains = [SyncDomain(d.lower()) for d in request.domains]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain in list. Valid domains: {[d.value for d in SyncDomain]}",
        )
    
    # Get integration credentials
    from app.modules.integrations.infrastructure.models import IntegrationConnectionModel
    integration = session.query(IntegrationConnectionModel).filter(
        IntegrationConnectionModel.company_id == request.company_id,
        IntegrationConnectionModel.provider == request.provider,
        IntegrationConnectionModel.enabled == True,
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active integration found for company {request.company_id} and provider {request.provider}",
        )
    
    # Build window_config from request or use defaults
    window_config = request.window_config if request.window_config else {d: 30 for d in request.domains}
    
    # Convert priority_config strings to JobPriority enum
    priority_config_converted = {}
    if request.priority_config:
        for domain, priority_str in request.priority_config.items():
            try:
                priority_config_converted[domain] = JobPriority(priority_str.lower())
            except ValueError:
                priority_config_converted[domain] = JobPriority.NORMAL
    
    batch = orchestrator.schedule_full_sync(
        company_id=request.company_id,
        provider=request.provider,
        domains=domains,
        encrypted_credentials=integration.credentials,
        window_config=window_config,
        priority_config=priority_config_converted if priority_config_converted else None,
    )
    
    return {
        "message": "Full sync scheduled",
        "batch_id": batch.batch_id,
        "total_jobs": len(batch.jobs),
        "jobs": [_job_to_response(job) for job in batch.jobs],
    }


@router.post("/schedule/incremental")
def schedule_incremental_sync(
    request: ScheduleIncrementalSyncRequest,
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
    session: Session = Depends(get_db),
) -> dict:
    """Schedule incremental synchronization for multiple domains."""
    try:
        domains = [SyncDomain(d.lower()) for d in request.domains]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain in list. Valid domains: {[d.value for d in SyncDomain]}",
        )
    
    # Get integration credentials
    from app.modules.integrations.infrastructure.models import IntegrationConnectionModel
    integration = session.query(IntegrationConnectionModel).filter(
        IntegrationConnectionModel.company_id == request.company_id,
        IntegrationConnectionModel.provider == request.provider,
        IntegrationConnectionModel.enabled == True,
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active integration found",
        )
    
    # Convert priority_config strings to JobPriority enum
    priority_config_converted = {}
    if request.priority_config:
        for domain, priority_str in request.priority_config.items():
            try:
                priority_config_converted[domain] = JobPriority(priority_str.lower())
            except ValueError:
                priority_config_converted[domain] = JobPriority.NORMAL
    
    batch = orchestrator.schedule_incremental_sync(
        company_id=request.company_id,
        provider=request.provider,
        domains=domains,
        encrypted_credentials=integration.credentials,
        priority_config=priority_config_converted if priority_config_converted else None,
    )
    
    return {
        "message": "Incremental sync scheduled",
        "batch_id": batch.batch_id,
        "total_jobs": len(batch.jobs),
        "jobs": [_job_to_response(job) for job in batch.jobs],
    }


@router.post("/schedule/domain")
def schedule_domain_sync(
    request: ScheduleDomainSyncRequest,
    orchestrator: SynchronizationOrchestrator = Depends(get_orchestrator),
    session: Session = Depends(get_db),
) -> dict:
    """Schedule synchronization for a specific domain."""
    try:
        domain = SyncDomain(request.domain.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain: {request.domain}. Valid domains: {[d.value for d in SyncDomain]}",
        )
    
    try:
        priority = JobPriority(request.priority.upper())
    except ValueError:
        priority = JobPriority.NORMAL
    
    # Find active integration for this company and provider
    from app.modules.integrations.infrastructure.models import IntegrationConnectionModel
    integration = session.query(IntegrationConnectionModel).filter(
        IntegrationConnectionModel.company_id == request.company_id,
        IntegrationConnectionModel.provider == request.provider,
        IntegrationConnectionModel.enabled == True,
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active integration found for company {request.company_id} and provider {request.provider}",
        )
    
    # Create window from request dates
    from datetime import timedelta
    
    if request.window_start and request.window_end:
        window = TimeWindow(
            start_date=request.window_start,
            end_date=request.window_end,
        )
    else:
        # Default: last 7 days
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        window = TimeWindow(start_date=start_date, end_date=end_date)
    
    job = orchestrator.schedule_domain_sync(
        company_id=request.company_id,
        provider=request.provider,
        domain=domain,
        encrypted_credentials=integration.credentials,
        mode=request.mode,
        window=window,
        priority=priority,
    )
    
    return {
        "message": "Domain sync scheduled",
        "job": _job_to_response(job),
    }


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
        )

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
