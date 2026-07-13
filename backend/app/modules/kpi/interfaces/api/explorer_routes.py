from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.kpi.application.explorer_service import KpiExplorerService
from app.modules.kpi.interfaces.api.explorer_schemas import KpiCatalogResponse, KpiDetailResponse, KpiExplorerListResponse
from app.shared.domain.errors import NotFoundError
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.tenant_guard import TenantGuard
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("", response_model=KpiExplorerListResponse)
def list_kpis(
    company_id: str | None = Query(default=None),
    period_ref: str | None = Query(default=None),
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> KpiExplorerListResponse:
    if company_id is not None:
        TenantGuard.assert_path_company(principal.company_id, company_id)
    tenant_id = company_id or principal.company_id

    tx = TransactionBoundary(db)
    payload = tx.execute(lambda: KpiExplorerService(db).list_kpis(company_id=tenant_id, period_ref=period_ref))
    return KpiExplorerListResponse.model_validate(payload)


@router.get("/catalog", response_model=KpiCatalogResponse)
def list_kpi_catalog(
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> KpiCatalogResponse:
    tx = TransactionBoundary(db)
    payload = tx.execute(lambda: KpiExplorerService(db).catalog())
    return KpiCatalogResponse.model_validate(payload)


@router.get("/{kpi_id}", response_model=KpiDetailResponse)
def get_kpi_detail(
    kpi_id: str,
    company_id: str | None = Query(default=None),
    period_ref: str | None = Query(default=None),
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> KpiDetailResponse:
    if company_id is not None:
        TenantGuard.assert_path_company(principal.company_id, company_id)
    tenant_id = company_id or principal.company_id

    tx = TransactionBoundary(db)
    payload = tx.execute(
        lambda: KpiExplorerService(db).get_kpi_detail(company_id=tenant_id, kpi_id=kpi_id, period_ref=period_ref)
    )
    if payload is None:
        raise ErrorMapper.not_found(NotFoundError("kpi not found"))
    return KpiDetailResponse.model_validate(payload)