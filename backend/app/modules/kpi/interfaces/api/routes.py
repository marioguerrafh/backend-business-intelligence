from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.kpi.application.use_cases import EvaluateFormulaUseCase
from app.modules.kpi.application.orchestrator_contracts import IngestCompletedEvent
from app.modules.kpi.domain.formula_engine_errors import FormulaEngineError
from app.modules.kpi.infrastructure.container import build_formula_engine_internal_api, build_kpi_orchestrator_use_case
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/kpi", tags=["kpi"])


class EvaluateFormulaRequest(BaseModel):
    formula_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    period_ref: str = Field(min_length=1)
    metrics: dict[str, Any]


class KPIOrchestratorIngestCompletedRequest(BaseModel):
    company_id: str = Field(min_length=1)
    import_job_id: str = Field(min_length=1)
    template: str = Field(
        pattern=(
            "^(customers|products|sales|cashflow|financial|balance_sheet|income_statement|"
            "accounts_receivable|accounts_payable|inventory|hr|procurement|service|production)$"
        )
    )
    source_system: str = Field(default="csv_official_template", min_length=1)
    event_id: str | None = None
    orchestrator_run_id: str | None = None
    period_ref: str | None = None
    correlation_id: str | None = None


class KPIOrchestratorPeriodResponse(BaseModel):
    period_ref: str
    orchestrator_run_id: str
    status: str
    recalculated_count: int
    failed_count: int
    idempotent_hit: bool
    published_event_ids: list[str]


class KPIOrchestratorRunResponse(BaseModel):
    source_event_topic: str
    source_event_id: str | None = None
    company_id: str
    import_job_id: str
    periods: list[KPIOrchestratorPeriodResponse]


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "kpi", "status": "ok"}


@router.post("/internal/formulas/evaluate")
def evaluate_formula(payload: EvaluateFormulaRequest) -> dict[str, object]:
    use_case = EvaluateFormulaUseCase(formula_engine_api=build_formula_engine_internal_api())
    try:
        return use_case.execute(
            formula_id=payload.formula_id,
            company_id=payload.company_id,
            period_ref=payload.period_ref,
            metrics=payload.metrics,
        )
    except FormulaEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/internal/orchestrator/ingest-completed", response_model=KPIOrchestratorRunResponse)
def orchestrate_kpi_recalculation(
    payload: KPIOrchestratorIngestCompletedRequest,
    db: Session = Depends(get_db),
) -> KPIOrchestratorRunResponse:
    use_case = build_kpi_orchestrator_use_case(db)
    tx = TransactionBoundary(db)

    try:
        result = tx.execute(
            lambda: use_case.execute(
                IngestCompletedEvent(
                    company_id=payload.company_id,
                    import_job_id=payload.import_job_id,
                    template=payload.template,
                    source_system=payload.source_system,
                    event_id=payload.event_id,
                    orchestrator_run_id=payload.orchestrator_run_id,
                    period_ref=payload.period_ref,
                    correlation_id=payload.correlation_id,
                )
            )
        )
    except (FormulaEngineError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return KPIOrchestratorRunResponse(
        source_event_topic=result.source_event_topic,
        source_event_id=result.source_event_id,
        company_id=result.company_id,
        import_job_id=result.import_job_id,
        periods=[
            KPIOrchestratorPeriodResponse(
                period_ref=item.period_ref,
                orchestrator_run_id=item.orchestrator_run_id,
                status=item.status,
                recalculated_count=item.recalculated_count,
                failed_count=item.failed_count,
                idempotent_hit=item.idempotent_hit,
                published_event_ids=list(item.published_event_ids),
            )
            for item in result.periods
        ],
    )
