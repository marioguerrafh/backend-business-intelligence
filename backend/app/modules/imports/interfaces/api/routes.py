import logging
from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.imports.application.contracts import ImportCsvCommand, ImportTemplate
from app.modules.imports.infrastructure.container import build_imports_container
from app.modules.imports.infrastructure.models import ImportJobModel
from app.modules.imports.interfaces.api.schemas import (
    ImportCsvResponse,
    ImportInconsistencyResponse,
    ImportJobStatusResponse,
)
from app.modules.pipeline.infrastructure.container import build_pipeline_container
from app.shared.infrastructure.db.session import SessionLocal
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.tenant_guard import TenantGuard
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/imports", tags=["imports"])
logger = logging.getLogger("app.imports")


def _trigger_pipeline_after_import(
    *,
    company_id: str,
    template: ImportTemplate,
    source_system: str,
    import_job_id: str,
    ingest_event_id: str | None,
    correlation_id: str | None,
) -> None:
    db = SessionLocal()
    tx = TransactionBoundary(db)
    try:
        pipeline_container = build_pipeline_container(db)
        tx.execute(
            lambda: pipeline_container.coordinator.consume_ingest_completed(
                company_id=company_id,
                import_job_id=import_job_id,
                template=template,
                source_system=source_system,
                event_id=ingest_event_id,
                correlation_id=correlation_id,
            )
        )
    except Exception:
        logger.exception("failed to trigger pipeline after import", extra={"import_job_id": import_job_id})
    finally:
        db.close()


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "imports", "status": "ok"}


@router.post("/csv", response_model=ImportCsvResponse)
def import_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    company_id: str = Form(...),
    template: str = Form(...),
    source_system: str = Form(default="csv_official_template"),
    file: UploadFile = File(...),
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ImportCsvResponse:
    TenantGuard.assert_payload_company(principal.company_id, company_id)

    allowed_templates = {
        "customers",
        "products",
        "sales",
        "cashflow",
        "balance_sheet",
        "income_statement",
        "accounts_receivable",
        "accounts_payable",
        "inventory",
        "hr",
        "financial",
    }
    if template not in allowed_templates:
        raise ErrorMapper.unprocessable(
            ValueError(
                "template must be one of customers, products, sales, cashflow, balance_sheet, "
                "income_statement, accounts_receivable, accounts_payable, inventory, hr, financial"
            )
        )
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ErrorMapper.unprocessable(ValueError("file must be a .csv"))

    import_template = cast(ImportTemplate, template)
    content = file.file.read().decode("utf-8-sig")
    container = build_imports_container(db, enable_pipeline=False)
    tx = TransactionBoundary(db)

    try:
        result = tx.execute(
            lambda: container.import_csv.execute(
                ImportCsvCommand(
                    company_id=company_id,
                    template=import_template,
                    source_system=source_system,
                    csv_content=content,
                    correlation_id=request.headers.get("X-Correlation-ID"),
                )
            )
        )
    except ValueError as exc:
        raise ErrorMapper.unprocessable(exc) from exc

    if result.status != "failed":
        background_tasks.add_task(
            _trigger_pipeline_after_import,
            company_id=company_id,
            template=result.template,
            source_system=source_system,
            import_job_id=result.job_id,
            ingest_event_id=result.ingest_event_id,
            correlation_id=request.headers.get("X-Correlation-ID"),
        )

    return ImportCsvResponse(
        job_id=result.job_id,
        template=import_template,
        status=result.status,
        total_rows=result.total_rows,
        imported_rows=result.imported_rows,
        failed_rows=result.failed_rows,
        ingest_event_id=result.ingest_event_id,
        inconsistencies=[
            ImportInconsistencyResponse(
                row_number=issue.row_number,
                field=issue.field,
                message=issue.message,
                raw_value=issue.raw_value,
            )
            for issue in result.inconsistencies
        ],
    )


@router.get("/jobs/{job_id}", response_model=ImportJobStatusResponse)
def get_import_job_status(
    job_id: str,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ImportJobStatusResponse:
    pipeline_container = build_pipeline_container(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: pipeline_container.service.get_import_job_progress(
                company_id=principal.company_id,
                job_id=job_id,
            )
        )
    except ValueError as exc:
        model = db.get(ImportJobModel, job_id)
        if model is None or model.company_id != principal.company_id:
            raise ErrorMapper.not_found(exc) from exc

        progress = 0
        if model.total_rows > 0:
            progress = int((model.imported_rows / model.total_rows) * 100)
        elif model.status in {"success", "partial", "failed"}:
            progress = 100

        return ImportJobStatusResponse(
            job_id=model.import_job_id,
            status=model.status,
            progress=progress,
            current_step="import_csv" if model.status == "running" else None,
            started_at=model.started_at,
            estimated_remaining_seconds=0,
            summary_updated=False,
        )

    return ImportJobStatusResponse(
        job_id=result.job_id,
        status=result.status,
        progress=result.progress,
        current_step=result.current_step,
        started_at=result.started_at,
        estimated_remaining_seconds=result.estimated_remaining_seconds,
        summary_updated=result.summary_updated,
    )
