from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from app.modules.summary.application.contracts import GetSummaryQuery
from app.modules.summary.application.ports.repository import SummaryProjectionRecord, SummaryRepository
from app.modules.summary.application.summary_builder import SummaryBuilder
from app.modules.summary.application.summary_cache import SummaryCache
from app.modules.summary.application.summary_projection import SummaryProjection
from app.shared.domain.errors import NotFoundError


@dataclass(slots=True, frozen=True)
class SummaryResult:
    payload: dict[str, object]
    cache_hit: bool


class SummaryService:
    def __init__(
        self,
        repository: SummaryRepository,
        builder: SummaryBuilder,
        projection: SummaryProjection,
        cache: SummaryCache,
    ) -> None:
        self.repository = repository
        self.builder = builder
        self.projection = projection
        self.cache = cache

    def get_summary(self, query: GetSummaryQuery) -> SummaryResult:
        started = perf_counter()
        cache_key = self._cache_key(query.company_id, query.period_ref)

        cached = self.cache.get(cache_key)
        if cached is not None:
            period_ref = str(cached["period_ref"])
            summary_id = str(cached["summary_id"])
            self.repository.audit_access(
                company_id=query.company_id,
                period_ref=period_ref,
                summary_id=summary_id,
                correlation_id=query.correlation_id,
                cache_hit=True,
                duration_ms=self._duration_ms(started),
            )
            return SummaryResult(payload=cached, cache_hit=True)

        projection = self.repository.get_projection(company_id=query.company_id, period_ref=query.period_ref)
        if projection is None:
            source = self.repository.load_source_payload(company_id=query.company_id, period_ref=query.period_ref)
            if source is None:
                raise NotFoundError("summary not found")
            aggregate = self.builder.build(summary_id=f"sum_{uuid4().hex[:16]}", source=source)
            self.repository.save_projection(aggregate)
            projection = self.projection.to_record(aggregate)

        payload = projection.payload
        self.cache.set(cache_key, payload)
        self.repository.audit_access(
            company_id=query.company_id,
            period_ref=projection.period_ref,
            summary_id=projection.summary_id,
            correlation_id=query.correlation_id,
            cache_hit=False,
            duration_ms=self._duration_ms(started),
        )
        return SummaryResult(payload=payload, cache_hit=False)

    @staticmethod
    def _cache_key(company_id: str, period_ref: str | None) -> str:
        return f"{company_id}:{period_ref or 'latest'}"

    @staticmethod
    def _duration_ms(started: float) -> int:
        return int((perf_counter() - started) * 1000)

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)
