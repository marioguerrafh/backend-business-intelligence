from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GenerateRecommendationsCommand:
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    source_event_id: str | None = None
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class GenerateRecommendationsResult:
    company_id: str
    period_ref: str
    orchestrator_run_id: str
    generated_count: int
    deduplicated_count: int
    grouped_count: int
    published_event_ids: tuple[str, ...]
