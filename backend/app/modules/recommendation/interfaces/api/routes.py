from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.recommendation.application.contracts import GenerateRecommendationsCommand
from app.modules.recommendation.domain.errors import RecommendationEngineError
from app.modules.recommendation.infrastructure.container import build_recommendation_engine_use_case
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/recommendation", tags=["recommendation"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "recommendation", "status": "ok"}


class GenerateRecommendationsRequest(BaseModel):
    company_id: str = Field(min_length=1)
    period_ref: str = Field(min_length=4)
    orchestrator_run_id: str = Field(min_length=1, max_length=64)
    source_event_id: str | None = None
    correlation_id: str | None = None


class GenerateRecommendationsResponse(BaseModel):
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    generated_count: int
    deduplicated_count: int
    grouped_count: int
    published_event_ids: list[str]


@router.post("/internal/generate", response_model=GenerateRecommendationsResponse)
def generate_recommendations(
    payload: GenerateRecommendationsRequest,
    db: Session = Depends(get_db),
) -> GenerateRecommendationsResponse:
    use_case = build_recommendation_engine_use_case(db)
    tx = TransactionBoundary(db)

    try:
        result = tx.execute(
            lambda: use_case.execute(
                GenerateRecommendationsCommand(
                    company_id=payload.company_id,
                    period_ref=payload.period_ref,
                    orchestrator_run_id=payload.orchestrator_run_id,
                    source_event_id=payload.source_event_id,
                    correlation_id=payload.correlation_id,
                )
            )
        )
    except RecommendationEngineError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return GenerateRecommendationsResponse(
        company_id=result.company_id,
        period_ref=result.period_ref,
        orchestrator_run_id=result.orchestrator_run_id,
        generated_count=result.generated_count,
        deduplicated_count=result.deduplicated_count,
        grouped_count=result.grouped_count,
        published_event_ids=list(result.published_event_ids),
    )
