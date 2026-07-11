from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.insight.application.contracts import GenerateInsightsCommand
from app.modules.insight.domain.errors import InsightEngineError
from app.modules.insight.infrastructure.container import build_insight_engine_use_case
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/insight", tags=["insight"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "insight", "status": "ok"}


class GenerateInsightsRequest(BaseModel):
    company_id: str = Field(min_length=1)
    period_ref: str = Field(min_length=4)
    orchestrator_run_id: str = Field(min_length=1, max_length=64)
    source_event_id: str | None = None
    correlation_id: str | None = None


class GenerateInsightsResponse(BaseModel):
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    generated_count: int
    published_event_ids: list[str]


@router.post("/internal/generate", response_model=GenerateInsightsResponse)
def generate_insights(payload: GenerateInsightsRequest, db: Session = Depends(get_db)) -> GenerateInsightsResponse:
    use_case = build_insight_engine_use_case(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: use_case.execute(
                GenerateInsightsCommand(
                    company_id=payload.company_id,
                    period_ref=payload.period_ref,
                    orchestrator_run_id=payload.orchestrator_run_id,
                    source_event_id=payload.source_event_id,
                    correlation_id=payload.correlation_id,
                )
            )
        )
    except InsightEngineError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return GenerateInsightsResponse(
        company_id=result.company_id,
        period_ref=result.period_ref,
        orchestrator_run_id=result.orchestrator_run_id,
        generated_count=result.generated_count,
        published_event_ids=list(result.published_event_ids),
    )
