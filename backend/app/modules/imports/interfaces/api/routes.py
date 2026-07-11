from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.imports.application.contracts import ImportCsvCommand
from app.modules.imports.infrastructure.container import build_imports_container
from app.modules.imports.interfaces.api.schemas import ImportCsvResponse
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.tenant_guard import TenantGuard
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "imports", "status": "ok"}


@router.post("/csv", response_model=ImportCsvResponse)
def import_csv(
    request: Request,
    company_id: str = Form(...),
    template: str = Form(...),
    source_system: str = Form(default="csv_official_template"),
    file: UploadFile = File(...),
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ImportCsvResponse:
    TenantGuard.assert_payload_company(principal.company_id, company_id)

    if template not in {"customers", "products", "sales", "financial"}:
        raise ErrorMapper.unprocessable(ValueError("template must be one of customers, products, sales, financial"))
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ErrorMapper.unprocessable(ValueError("file must be a .csv"))

    content = file.file.read().decode("utf-8-sig")

    container = build_imports_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: container.import_csv.execute(
                ImportCsvCommand(
                    company_id=company_id,
                    template=template,
                    source_system=source_system,
                    csv_content=content,
                    correlation_id=request.headers.get("X-Correlation-ID"),
                )
            )
        )
    except ValueError as exc:
        raise ErrorMapper.unprocessable(exc) from exc

    return ImportCsvResponse(
        job_id=result.job_id,
        template=result.template,
        status=result.status,
        total_rows=result.total_rows,
        imported_rows=result.imported_rows,
        failed_rows=result.failed_rows,
        ingest_event_id=result.ingest_event_id,
        inconsistencies=[
            {
                "row_number": issue.row_number,
                "field": issue.field,
                "message": issue.message,
                "raw_value": issue.raw_value,
            }
            for issue in result.inconsistencies
        ],
    )
