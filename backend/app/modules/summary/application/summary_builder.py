from __future__ import annotations

from app.modules.summary.application.ports.repository import SummarySourcePayload
from app.modules.summary.domain.entities import (
    SummaryAggregate,
    SummaryAlert,
    SummaryComparisons,
    SummaryInsight,
    SummaryKPI,
    SummaryRecommendation,
    SummaryScores,
    TimelinePoint,
)


class SummaryBuilder:
    def build(self, *, summary_id: str, source: SummarySourcePayload) -> SummaryAggregate:
        points = tuple(
            TimelinePoint(
                snapshot_date=str(point["snapshot_date"]),
                overall_score=float(point["overall_score"]),
                financial_score=self._optional_float(point.get("financial_score")),
                commercial_score=self._optional_float(point.get("commercial_score")),
                operational_score=self._optional_float(point.get("operational_score")),
            )
            for point in source.timeline_points
        )

        trend = self._build_comparisons(points)

        return SummaryAggregate(
            summary_id=summary_id,
            company_id=source.company_id,
            period_ref=source.period_ref,
            generated_at=source.generated_at,
            scores=SummaryScores(
                overall=float(source.scores["overall"]),
                financial=float(source.scores["financial"]),
                commercial=float(source.scores["commercial"]),
                operational=float(source.scores["operational"]),
            ),
            kpis=tuple(
                SummaryKPI(
                    kpi_id=str(item["kpi_id"]),
                    name=str(item.get("name") or item["kpi_id"]),
                    value=float(item["value"]),
                    unit=self._optional_str(item.get("unit")),
                    trend=self._optional_str(item.get("trend")),
                    health=self._optional_str(item.get("health")),
                )
                for item in source.kpis
            ),
            alerts=tuple(
                SummaryAlert(
                    alert_id=str(item["alert_id"]),
                    kpi_id=str(item.get("kpi_id") or ""),
                    rule_id=str(item.get("rule_id") or ""),
                    rule_name=str(item.get("rule_name") or ""),
                    severity=str(item["severity"]),
                    priority=str(item["priority"]),
                    metric_value=self._optional_float(item.get("metric_value")),
                    category=self._optional_str(item.get("category")),
                    probability=self._optional_float(item.get("probability")),
                    impact=self._optional_float(item.get("impact")),
                    related_recommendation_ids=tuple(str(x) for x in (item.get("related_recommendation_ids") or [])),
                    title=str(item["title"]),
                    description=str(item.get("description") or ""),
                )
                for item in source.alerts
            ),
            insights=tuple(
                SummaryInsight(
                    insight_id=str(item["insight_id"]),
                    insight_type=str(item["type"]),
                    statement=str(item["statement"]),
                    evidence=dict(item.get("evidence") or {}),
                    related_kpis=tuple(str(x) for x in (item.get("related_kpis") or [])),
                    related_rules=tuple(str(x) for x in (item.get("related_rules") or [])),
                    related_recommendations=tuple(str(x) for x in (item.get("related_recommendations") or [])),
                )
                for item in source.insights
            ),
            recommendations=tuple(
                SummaryRecommendation(
                    recommendation_id=str(item["recommendation_id"]),
                    title=str(item["title"]),
                    rank=float(item["rank"]),
                    expected_impact=dict(item.get("expected_impact") or {}),
                    owner_role=self._optional_str(item.get("owner_role")),
                    sla_target=self._optional_str(item.get("sla_target")),
                    related_kpis=tuple(str(x) for x in (item.get("related_kpis") or [])),
                    related_rules=tuple(str(x) for x in (item.get("related_rules") or [])),
                )
                for item in source.recommendations
            ),
            trends=trend,
            next_risks=source.next_risks,
            timeline_points=points,
            dashboard=dict(source.dashboard),
        )

    @staticmethod
    def _build_comparisons(points: tuple[TimelinePoint, ...]) -> SummaryComparisons:
        if not points:
            return SummaryComparisons(
                today_vs_yesterday=None,
                today_vs_last_month=None,
                today_vs_last_year=None,
            )

        latest = points[0].overall_score
        prev_day = points[1].overall_score if len(points) > 1 else None
        prev_month = points[2].overall_score if len(points) > 2 else None
        prev_year = points[3].overall_score if len(points) > 3 else None

        return SummaryComparisons(
            today_vs_yesterday=(latest - prev_day) if prev_day is not None else None,
            today_vs_last_month=(latest - prev_month) if prev_month is not None else None,
            today_vs_last_year=(latest - prev_year) if prev_year is not None else None,
        )

    @staticmethod
    def _optional_str(value: object | None) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _optional_float(value: object | None) -> float | None:
        if value is None:
            return None
        return float(value)
