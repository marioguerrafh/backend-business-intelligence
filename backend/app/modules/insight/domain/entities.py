from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class PromptTemplateDefinition:
    prompt_id: str
    intent: str
    audience: str
    language: str
    output_schema: str
    guardrails: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class InsightAggregate:
    insight_result_id: str
    company_id: str
    period_ref: str
    insight_type: str
    statement: str
    evidence: dict[str, Any]
    prompt_id: str
    orchestrator_run_id: str
    generated_at: datetime
