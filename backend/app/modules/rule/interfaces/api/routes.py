from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.rule.application.contracts import ExecuteRulesCommand
from app.modules.rule.domain.errors import RuleEngineError
from app.modules.rule.infrastructure.container import build_rule_engine_use_case
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/rule", tags=["rule"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "rule", "status": "ok"}


class ExecuteRulesRequest(BaseModel):
    company_id: str = Field(min_length=1)
    period_ref: str = Field(min_length=4)
    orchestrator_run_id: str = Field(min_length=1, max_length=64)
    correlation_id: str | None = None
    source_event_id: str | None = None


class ExecuteRulesResponse(BaseModel):
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    evaluated_rules: int
    fired_rules: int
    idempotent_hits: int
    published_event_ids: list[str]


@router.post("/internal/execute", response_model=ExecuteRulesResponse)
def execute_rules(payload: ExecuteRulesRequest, db: Session = Depends(get_db)) -> ExecuteRulesResponse:
    use_case = build_rule_engine_use_case(db)
    tx = TransactionBoundary(db)
    try:
        result = tx.execute(
            lambda: use_case.execute(
                ExecuteRulesCommand(
                    company_id=payload.company_id,
                    period_ref=payload.period_ref,
                    orchestrator_run_id=payload.orchestrator_run_id,
                    correlation_id=payload.correlation_id,
                    source_event_id=payload.source_event_id,
                )
            )
        )
    except RuleEngineError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return ExecuteRulesResponse(
        company_id=result.company_id,
        period_ref=result.period_ref,
        orchestrator_run_id=result.orchestrator_run_id,
        evaluated_rules=result.evaluated_rules,
        fired_rules=result.fired_rules,
        idempotent_hits=result.idempotent_hits,
        published_event_ids=list(result.published_event_ids),
    )
