from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.presenter import ExecutivePresentationMapper
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


def _presenter() -> ExecutivePresentationMapper:
    return ExecutivePresentationMapper(catalog_reader=PresentationCatalog())


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
        dashboard={
            "last_import": None,
            "last_pipeline": "completed",
            "pipeline_duration_ms": 3200,
            "summary_version": "3.1",
            "refresh_interval_seconds": 300,
            "data_quality": "excellent",
        },
    )


def test_summary_service_builds_projection_and_audits() -> None:
    repo = _Repo(projection=None, source=_source(), audited=[])
    service = SummaryService(
        repository=repo,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=InMemorySummaryCache(ttl_seconds=120),
        presenter=_presenter(),
    )

    result = service.get_summary(GetSummaryQuery(company_id="cmp_acme", period_ref="2026-07"))

    assert result.cache_hit is False
    assert result.payload["company_id"] == "cmp_acme"
    assert "executive_score" in result.payload["scores"]
    assert repo.projection is not None
    assert repo.audited[-1]["cache_hit"] is False


def test_summary_service_cache_hit_on_second_read() -> None:
    repo = _Repo(projection=None, source=_source(), audited=[])
    service = SummaryService(
        repository=repo,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=InMemorySummaryCache(ttl_seconds=120),
        presenter=_presenter(),
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
        presenter=_presenter(),
    )

    with pytest.raises(NotFoundError):
        service.get_summary(GetSummaryQuery(company_id="cmp_unknown"))


def test_summary_service_force_refresh_bypasses_stale_projection_and_cache() -> None:
    stale_projection = SummaryProjectionRecord(
        summary_id="sum_stale",
        company_id="cmp_acme",
        period_ref="2026-07",
        payload={
            "summary_id": "sum_stale",
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "generated_at": "2026-07-10T00:00:00+00:00",
            "scores": {
                "overall": 80,
                "financial": 80,
                "commercial": 80,
                "operational": 80,
            },
            "kpis": [],
            "alerts": [],
            "insights": [],
            "recommendations": [],
            "trends": {
                "today_vs_yesterday": None,
                "today_vs_last_month": None,
                "today_vs_last_year": None,
            },
            "next_risks": [],
            "timeline": {"points": []},
        },
        generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )

    source = SummarySourcePayload(
        company_id="cmp_acme",
        period_ref="2026-07",
        generated_at=datetime(2026, 7, 12, tzinfo=timezone.utc),
        scores={"overall": 81, "financial": 82, "commercial": 79, "operational": 80},
        kpis=(
            {
                "kpi_id": "kpi.margin",
                "name": "Margem",
                "value": 22.5,
                "unit": "%",
                "trend": "up",
                "health": "green",
            },
        ),
        alerts=(),
        insights=(),
        recommendations=(),
        timeline_points=(),
        next_risks=(),
        dashboard={
            "last_import": None,
            "last_pipeline": "completed",
            "pipeline_duration_ms": 3200,
            "summary_version": "3.1",
            "refresh_interval_seconds": 300,
            "data_quality": "excellent",
        },
    )

    repo = _Repo(projection=stale_projection, source=source, audited=[])
    service = SummaryService(
        repository=repo,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=InMemorySummaryCache(ttl_seconds=120),
        presenter=_presenter(),
    )

    # Warm cache with stale projection path.
    stale = service.get_summary(GetSummaryQuery(company_id="cmp_acme", period_ref="2026-07"))
    assert stale.cache_hit is False
    assert stale.payload["kpis"] == []

    refreshed = service.get_summary(
        GetSummaryQuery(company_id="cmp_acme", period_ref="2026-07", force_refresh=True)
    )

    assert refreshed.cache_hit is False
    assert len(refreshed.payload["kpis"]) == 1
    assert refreshed.payload["kpis"][0]["id"] == "kpi.margin"
