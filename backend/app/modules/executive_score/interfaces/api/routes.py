from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.executive_score.application.contracts import CalculateExecutiveScoreCommand
from app.modules.executive_score.domain.errors import ExecutiveScoreEngineError
from app.modules.executive_score.infrastructure.container import build_executive_score_use_case
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/executive-score", tags=["executive-score"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "executive-score", "status": "ok"}


class CalculateExecutiveScoreRequest(BaseModel):
    company_id: str = Field(min_length=1)
    period_ref: str = Field(min_length=4)
    orchestrator_run_id: str = Field(min_length=1, max_length=64)
    source_event_id: str | None = None
    correlation_id: str | None = None


class CalculateExecutiveScoreResponse(BaseModel):
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    financial_score: float
    commercial_score: float
    operational_score: float
    inventory_score: float
    executive_score: float
    published_event_id: str


@router.post("/internal/calculate", response_model=CalculateExecutiveScoreResponse)
def calculate_executive_score(
    payload: CalculateExecutiveScoreRequest,
    db: Session = Depends(get_db),
) -> CalculateExecutiveScoreResponse:
    use_case = build_executive_score_use_case(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: use_case.execute(
                CalculateExecutiveScoreCommand(
                    company_id=payload.company_id,
                    period_ref=payload.period_ref,
                    orchestrator_run_id=payload.orchestrator_run_id,
                    source_event_id=payload.source_event_id,
                    correlation_id=payload.correlation_id,
                )
            )
        )
    except ExecutiveScoreEngineError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return CalculateExecutiveScoreResponse(
        company_id=result.company_id,
        period_ref=result.period_ref,
        orchestrator_run_id=result.orchestrator_run_id,
        financial_score=result.financial_score,
        commercial_score=result.commercial_score,
        operational_score=result.operational_score,
        inventory_score=result.inventory_score,
        executive_score=result.executive_score,
        published_event_id=result.published_event_id,
    )
