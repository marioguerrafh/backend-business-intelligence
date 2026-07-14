from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.integrations.application.contracts import ConnectIntegrationCommand, RunIntegrationSyncCommand
from app.modules.integrations.infrastructure.container import build_integrations_container
from app.modules.integrations.interfaces.api.schemas import (
    ConnectIntegrationRequest,
    IntegrationConnectionResponse,
    IntegrationSyncJobResponse,
)
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/connect", response_model=IntegrationConnectionResponse)
def connect_integration(
    payload: ConnectIntegrationRequest,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> IntegrationConnectionResponse:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: container.service.connect(
                ConnectIntegrationCommand(
                    company_id=principal.company_id,
                    provider=payload.provider,
                    credentials=payload.credentials,
                )
            )
        )
    except ValueError as exc:
        raise ErrorMapper.unprocessable(exc) from exc
    return IntegrationConnectionResponse(
        id=result.id,
        company_id=result.company_id,
        provider=result.provider,
        status=result.status,
        enabled=result.enabled,
        last_sync=result.last_sync,
        last_success_sync=result.last_success_sync,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("", response_model=list[IntegrationConnectionResponse])
def list_integrations(
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> list[IntegrationConnectionResponse]:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    result = tx.execute(lambda: container.service.list_integrations(company_id=principal.company_id))
    return [
        IntegrationConnectionResponse(
            id=item.id,
            company_id=item.company_id,
            provider=item.provider,
            status=item.status,
            enabled=item.enabled,
            last_sync=item.last_sync,
            last_success_sync=item.last_success_sync,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in result
    ]


@router.get("/{integration_id}", response_model=IntegrationConnectionResponse)
def get_integration(
    integration_id: str,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> IntegrationConnectionResponse:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: container.service.get_integration(company_id=principal.company_id, integration_id=integration_id)
        )
    except ValueError as exc:
        raise ErrorMapper.not_found(exc) from exc
    return IntegrationConnectionResponse(
        id=result.id,
        company_id=result.company_id,
        provider=result.provider,
        status=result.status,
        enabled=result.enabled,
        last_sync=result.last_sync,
        last_success_sync=result.last_success_sync,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.post("/{integration_id}/sync", response_model=IntegrationSyncJobResponse)
def run_incremental_sync(
    integration_id: str,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> IntegrationSyncJobResponse:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: container.service.sync(
                RunIntegrationSyncCommand(
                    company_id=principal.company_id,
                    integration_id=integration_id,
                    mode="incremental",
                )
            )
        )
    except ValueError as exc:
        raise ErrorMapper.unprocessable(exc) from exc
    return IntegrationSyncJobResponse(
        job_id=result.job_id,
        provider=result.provider,
        company_id=result.company_id,
        status=result.status,
        started_at=result.started_at,
        finished_at=result.finished_at,
        duration_ms=result.duration_ms,
        records_read=result.records_read,
        records_imported=result.records_imported,
        records_failed=result.records_failed,
        pipeline_run_id=result.pipeline_run_id,
    )


@router.post("/{integration_id}/full-sync", response_model=IntegrationSyncJobResponse)
def run_full_sync(
    integration_id: str,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> IntegrationSyncJobResponse:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: container.service.sync(
                RunIntegrationSyncCommand(
                    company_id=principal.company_id,
                    integration_id=integration_id,
                    mode="full",
                )
            )
        )
    except ValueError as exc:
        raise ErrorMapper.unprocessable(exc) from exc
    return IntegrationSyncJobResponse(
        job_id=result.job_id,
        provider=result.provider,
        company_id=result.company_id,
        status=result.status,
        started_at=result.started_at,
        finished_at=result.finished_at,
        duration_ms=result.duration_ms,
        records_read=result.records_read,
        records_imported=result.records_imported,
        records_failed=result.records_failed,
        pipeline_run_id=result.pipeline_run_id,
    )


@router.get("/jobs", response_model=list[IntegrationSyncJobResponse])
def list_jobs(
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> list[IntegrationSyncJobResponse]:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    result = tx.execute(lambda: container.service.list_jobs(company_id=principal.company_id))
    return [
        IntegrationSyncJobResponse(
            job_id=item.job_id,
            provider=item.provider,
            company_id=item.company_id,
            status=item.status,
            started_at=item.started_at,
            finished_at=item.finished_at,
            duration_ms=item.duration_ms,
            records_read=item.records_read,
            records_imported=item.records_imported,
            records_failed=item.records_failed,
            pipeline_run_id=item.pipeline_run_id,
        )
        for item in result
    ]


@router.get("/jobs/{job_id}", response_model=IntegrationSyncJobResponse)
def get_job(
    job_id: str,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> IntegrationSyncJobResponse:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(lambda: container.service.get_job(company_id=principal.company_id, job_id=job_id))
    except ValueError as exc:
        raise ErrorMapper.not_found(exc) from exc
    return IntegrationSyncJobResponse(
        job_id=result.job_id,
        provider=result.provider,
        company_id=result.company_id,
        status=result.status,
        started_at=result.started_at,
        finished_at=result.finished_at,
        duration_ms=result.duration_ms,
        records_read=result.records_read,
        records_imported=result.records_imported,
        records_failed=result.records_failed,
        pipeline_run_id=result.pipeline_run_id,
    )


@router.delete("/{integration_id}")
def disconnect_integration(
    integration_id: str,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    container = build_integrations_container(db)
    tx = TransactionBoundary(db)
    try:
        tx.execute(lambda: container.service.disconnect(company_id=principal.company_id, integration_id=integration_id))
    except ValueError as exc:
        raise ErrorMapper.not_found(exc) from exc
    return {"status": "disconnected", "integration_id": integration_id}
