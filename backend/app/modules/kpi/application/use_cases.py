from dataclasses import asdict

from app.modules.kpi.application.formula_engine_api import FormulaEngineInternalAPI
from app.modules.kpi.domain.formula_engine_entities import FormulaEvaluationRequest


class KPIUseCase:
    def execute(self) -> dict[str, str]:
        return {"module": "kpi", "status": "initialized"}


class EvaluateFormulaUseCase:
    """Use case exposing Formula Engine internal API to KPI module."""

    def __init__(self, formula_engine_api: FormulaEngineInternalAPI) -> None:
        self.formula_engine_api = formula_engine_api

    def execute(
        self,
        *,
        formula_id: str,
        company_id: str,
        period_ref: str,
        metrics: dict[str, object],
    ) -> dict[str, object]:
        result = self.formula_engine_api.evaluate_formula(
            FormulaEvaluationRequest(
                formula_id=formula_id,
                company_id=company_id,
                period_ref=period_ref,
                metrics=metrics,
            )
        )
        payload = asdict(result)
        payload["audit"]["executed_at"] = result.audit.executed_at.isoformat()
        return payload
