from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class RuleDefinition:
    rule_id: str
    kpi_id: str
    name: str
    condition: str
    severity: str
    priority: str
    enabled: bool


@dataclass(slots=True, frozen=True)
class KPIValue:
    kpi_id: str
    value: float


@dataclass(slots=True, frozen=True)
class RuleExecutionAudit:
    rule_id: str
    kpi_id: str
    company_id: str
    period_ref: str
    status: str
    expression: str
    evaluation_trace: list[str]
    fired: bool
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class RuleExecutionResult:
    alert_id: str
    rule_id: str
    kpi_id: str
    company_id: str
    period_ref: str
    severity: str
    priority: str
    title: str
    description: str
    metric_value: float
    fired_at: datetime
    orchestrator_run_id: str
