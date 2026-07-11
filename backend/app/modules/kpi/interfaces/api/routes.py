from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.modules.kpi.application.use_cases import EvaluateFormulaUseCase
from app.modules.kpi.domain.formula_engine_errors import FormulaEngineError
from app.modules.kpi.infrastructure.container import build_formula_engine_internal_api

router = APIRouter(prefix="/kpi", tags=["kpi"])


class EvaluateFormulaRequest(BaseModel):
    formula_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    period_ref: str = Field(min_length=1)
    metrics: dict[str, Any]


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
