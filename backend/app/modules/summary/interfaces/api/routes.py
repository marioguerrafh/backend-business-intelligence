from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.summary.application.contracts import GetSummaryQuery
from app.modules.summary.infrastructure.container import build_summary_container
from app.modules.summary.interfaces.api.schemas import GetSummaryResponse
from app.shared.domain.errors import NotFoundError
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.tenant_guard import TenantGuard
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("", response_model=GetSummaryResponse)
def get_summary(
    request: Request,
    company_id: str | None = Query(default=None),
    period_ref: str | None = Query(default=None),
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> GetSummaryResponse:
    if company_id is not None:
        TenantGuard.assert_path_company(principal.company_id, company_id)

    tenant_id = company_id or principal.company_id

    container = build_summary_container(db)
    tx = TransactionBoundary(db)

    try:
        result = tx.execute(
            lambda: container.service.get_summary(
                GetSummaryQuery(
                    company_id=tenant_id,
                    period_ref=period_ref,
                    correlation_id=request.headers.get("X-Correlation-ID"),
                )
            )
        )
    except NotFoundError as exc:
        raise ErrorMapper.not_found(exc) from exc

    return GetSummaryResponse.model_validate(result.payload)
