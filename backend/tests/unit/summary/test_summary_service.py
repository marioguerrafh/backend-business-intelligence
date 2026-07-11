from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.modules.summary.application.contracts import GetSummaryQuery
from app.modules.summary.application.ports.repository import (
    SummaryProjectionRecord,
    SummaryRepository,
    SummarySourcePayload,
)
from app.modules.summary.application.summary_builder import SummaryBuilder
from app.modules.summary.application.summary_cache import InMemorySummaryCache
from app.modules.summary.application.summary_projection import SummaryProjection
from app.modules.summary.application.summary_service import SummaryService
from app.shared.domain.errors import NotFoundError


@dataclass
class _Repo(SummaryRepository):
    projection: SummaryProjectionRecord | None
    source: SummarySourcePayload | None
    audited: list[dict]

    def get_projection(self, *, company_id: str, period_ref: str | None) -> SummaryProjectionRecord | None:
        return self.projection

    def load_source_payload(self, *, company_id: str, period_ref: str | None) -> SummarySourcePayload | None:
        return self.source

    def save_projection(self, aggregate) -> None:
        self.projection = SummaryProjectionRecord(
            summary_id=aggregate.summary_id,
            company_id=aggregate.company_id,
            period_ref=aggregate.period_ref,
            payload=aggregate.to_payload(),
            generated_at=aggregate.generated_at,
        )

    def audit_access(self, **kwargs) -> None:
        self.audited.append(kwargs)


def _source() -> SummarySourcePayload:
    return SummarySourcePayload(
        company_id="cmp_acme",
        period_ref="2026-07",
        generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
        scores={"overall": 80, "financial": 80, "commercial": 80, "operational": 80},
        kpis=(),
        alerts=(),
        insights=(),
        recommendations=(),
        timeline_points=(),
        next_risks=(),
    )


def test_summary_service_builds_projection_and_audits() -> None:
    repo = _Repo(projection=None, source=_source(), audited=[])
    service = SummaryService(
        repository=repo,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=InMemorySummaryCache(ttl_seconds=120),
    )

    result = service.get_summary(GetSummaryQuery(company_id="cmp_acme", period_ref="2026-07"))

    assert result.cache_hit is False
    assert result.payload["company_id"] == "cmp_acme"
    assert repo.projection is not None
    assert repo.audited[-1]["cache_hit"] is False


def test_summary_service_cache_hit_on_second_read() -> None:
    repo = _Repo(projection=None, source=_source(), audited=[])
    service = SummaryService(
        repository=repo,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=InMemorySummaryCache(ttl_seconds=120),
    )

    service.get_summary(GetSummaryQuery(company_id="cmp_acme", period_ref="2026-07"))
    second = service.get_summary(GetSummaryQuery(company_id="cmp_acme", period_ref="2026-07"))

    assert second.cache_hit is True
    assert repo.audited[-1]["cache_hit"] is True


def test_summary_service_not_found_when_no_source() -> None:
    repo = _Repo(projection=None, source=None, audited=[])
    service = SummaryService(
        repository=repo,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=InMemorySummaryCache(ttl_seconds=120),
    )

    with pytest.raises(NotFoundError):
        service.get_summary(GetSummaryQuery(company_id="cmp_unknown"))
