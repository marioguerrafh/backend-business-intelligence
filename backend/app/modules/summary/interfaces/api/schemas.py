from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SummaryScoresResponse(BaseModel):
    overall: float
    financial: float
    commercial: float
    operational: float


class SummaryKPIResponse(BaseModel):
    kpi_id: str
    name: str
    value: float
    unit: str | None = None
    trend: str | None = None
    health: str | None = None


class SummaryAlertResponse(BaseModel):
    alert_id: str
    severity: str
    priority: str
    title: str
    description: str


class SummaryInsightResponse(BaseModel):
    insight_id: str
    type: str
    statement: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class SummaryRecommendationResponse(BaseModel):
    recommendation_id: str
    title: str
    rank: float
    expected_impact: dict[str, Any] = Field(default_factory=dict)
    owner_role: str | None = None
    sla_target: str | None = None


class SummaryTrendsResponse(BaseModel):
    today_vs_yesterday: float | None = None
    today_vs_last_month: float | None = None
    today_vs_last_year: float | None = None


class SummaryTimelinePointResponse(BaseModel):
    snapshot_date: str
    overall_score: float
    financial_score: float | None = None
    commercial_score: float | None = None
    operational_score: float | None = None


class SummaryTimelineResponse(BaseModel):
    points: list[SummaryTimelinePointResponse]


class GetSummaryResponse(BaseModel):
    summary_id: str
    company_id: str
    period_ref: str
    generated_at: str
    scores: SummaryScoresResponse
    kpis: list[SummaryKPIResponse]
    alerts: list[SummaryAlertResponse]
    insights: list[SummaryInsightResponse]
    recommendations: list[SummaryRecommendationResponse]
    trends: SummaryTrendsResponse
    next_risks: list[dict[str, Any]]
    timeline: SummaryTimelineResponse
