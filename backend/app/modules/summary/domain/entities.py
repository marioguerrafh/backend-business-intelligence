from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class SummaryScores:
    overall: float
    financial: float
    commercial: float
    operational: float


@dataclass(slots=True, frozen=True)
class SummaryKPI:
    kpi_id: str
    name: str
    value: float
    unit: str | None
    trend: str | None
    health: str | None


@dataclass(slots=True, frozen=True)
class SummaryAlert:
    alert_id: str
    kpi_id: str
    rule_id: str
    rule_name: str
    severity: str
    priority: str
    metric_value: float | None
    category: str | None
    probability: float | None
    impact: float | None
    related_recommendation_ids: tuple[str, ...]
    title: str
    description: str


@dataclass(slots=True, frozen=True)
class SummaryInsight:
    insight_id: str
    insight_type: str
    statement: str
    evidence: dict[str, Any]
    related_kpis: tuple[str, ...]
    related_rules: tuple[str, ...]
    related_recommendations: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class SummaryRecommendation:
    recommendation_id: str
    title: str
    rank: float
    expected_impact: dict[str, Any]
    owner_role: str | None
    sla_target: str | None
    related_kpis: tuple[str, ...]
    related_rules: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class SummaryComparisons:
    today_vs_yesterday: float | None
    today_vs_last_month: float | None
    today_vs_last_year: float | None


@dataclass(slots=True, frozen=True)
class TimelinePoint:
    snapshot_date: str
    overall_score: float
    financial_score: float | None
    commercial_score: float | None
    operational_score: float | None


@dataclass(slots=True, frozen=True)
class SummaryAggregate:
    summary_id: str
    company_id: str
    period_ref: str
    generated_at: datetime
    scores: SummaryScores
    kpis: tuple[SummaryKPI, ...]
    alerts: tuple[SummaryAlert, ...]
    insights: tuple[SummaryInsight, ...]
    recommendations: tuple[SummaryRecommendation, ...]
    trends: SummaryComparisons
    next_risks: tuple[dict[str, Any], ...]
    timeline_points: tuple[TimelinePoint, ...]
    dashboard: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "company_id": self.company_id,
            "period_ref": self.period_ref,
            "generated_at": self.generated_at.isoformat(),
            "scores": {
                "overall": self.scores.overall,
                "financial": self.scores.financial,
                "commercial": self.scores.commercial,
                "operational": self.scores.operational,
            },
            "kpis": [
                {
                    "kpi_id": item.kpi_id,
                    "name": item.name,
                    "value": item.value,
                    "unit": item.unit,
                    "trend": item.trend,
                    "health": item.health,
                }
                for item in self.kpis
            ],
            "alerts": [
                {
                    "alert_id": item.alert_id,
                    "kpi_id": item.kpi_id,
                    "rule_id": item.rule_id,
                    "rule_name": item.rule_name,
                    "severity": item.severity,
                    "priority": item.priority,
                    "metric_value": item.metric_value,
                    "category": item.category,
                    "probability": item.probability,
                    "impact": item.impact,
                    "related_recommendation_ids": list(item.related_recommendation_ids),
                    "title": item.title,
                    "description": item.description,
                }
                for item in self.alerts
            ],
            "insights": [
                {
                    "insight_id": item.insight_id,
                    "type": item.insight_type,
                    "statement": item.statement,
                    "evidence": item.evidence,
                    "related_kpis": list(item.related_kpis),
                    "related_rules": list(item.related_rules),
                    "related_recommendations": list(item.related_recommendations),
                }
                for item in self.insights
            ],
            "recommendations": [
                {
                    "recommendation_id": item.recommendation_id,
                    "title": item.title,
                    "rank": item.rank,
                    "expected_impact": item.expected_impact,
                    "owner_role": item.owner_role,
                    "sla_target": item.sla_target,
                    "related_kpis": list(item.related_kpis),
                    "related_rules": list(item.related_rules),
                }
                for item in self.recommendations
            ],
            "trends": {
                "today_vs_yesterday": self.trends.today_vs_yesterday,
                "today_vs_last_month": self.trends.today_vs_last_month,
                "today_vs_last_year": self.trends.today_vs_last_year,
            },
            "next_risks": list(self.next_risks),
            "timeline": {
                "points": [
                    {
                        "snapshot_date": point.snapshot_date,
                        "overall_score": point.overall_score,
                        "financial_score": point.financial_score,
                        "commercial_score": point.commercial_score,
                        "operational_score": point.operational_score,
                    }
                    for point in self.timeline_points
                ]
            },
            "dashboard": dict(self.dashboard),
        }
