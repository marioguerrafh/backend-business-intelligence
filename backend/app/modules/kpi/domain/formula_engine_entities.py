from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, frozen=True)
class FormulaDefinition:
    formula_id: str
    kpi_id: str
    name: str
    expression: str
    input_metrics: tuple[str, ...]
    output_type: str
    output_unit: str
    precision: int
    owner: str
    version: int
    effective_from: str = "1970-01-01"


@dataclass(slots=True)
class FormulaEvaluationRequest:
    formula_id: str
    company_id: str
    period_ref: str
    metrics: dict[str, Any]


@dataclass(slots=True)
class FormulaAuditRecord:
    formula_id: str
    company_id: str
    period_ref: str
    expression: str
    dependencies: list[str]
    inputs_used: dict[str, Any]
    execution_steps: list[str]
    result_value: float
    output_unit: str
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class FormulaEvaluationResult:
    formula_id: str
    kpi_id: str
    value: float
    unit: str
    precision: int
    audit: FormulaAuditRecord
