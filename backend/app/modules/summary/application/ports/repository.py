from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from app.modules.summary.domain.entities import SummaryAggregate


@dataclass(slots=True, frozen=True)
class SummarySourcePayload:
    company_id: str
    period_ref: str
    generated_at: datetime
    scores: dict[str, float]
    kpis: tuple[dict[str, Any], ...]
    alerts: tuple[dict[str, Any], ...]
    insights: tuple[dict[str, Any], ...]
    recommendations: tuple[dict[str, Any], ...]
    timeline_points: tuple[dict[str, Any], ...]
    next_risks: tuple[dict[str, Any], ...]
    dashboard: dict[str, Any]


@dataclass(slots=True, frozen=True)
class SummaryProjectionRecord:
    summary_id: str
    company_id: str
    period_ref: str
    payload: dict[str, Any]
    generated_at: datetime


class SummaryRepository(Protocol):
    def get_projection(self, *, company_id: str, period_ref: str | None) -> SummaryProjectionRecord | None:
        ...

    def load_source_payload(self, *, company_id: str, period_ref: str | None) -> SummarySourcePayload | None:
        ...

    def save_projection(self, aggregate: SummaryAggregate) -> None:
        ...

    def audit_access(
        self,
        *,
        company_id: str,
        period_ref: str,
        summary_id: str,
        correlation_id: str | None,
        cache_hit: bool,
        duration_ms: int,
    ) -> None:
        ...
