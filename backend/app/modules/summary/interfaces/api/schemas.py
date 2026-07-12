from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExecutiveScoreResponse(BaseModel):
    overall: float
    display: str
    status: str
    status_description: str
    color: str
    icon: str
    status_color: str
    status_icon: str
    variation: str
    comparison: str
    description: str


class ScoreDimensionResponse(BaseModel):
    label: str
    value: float
    display: str
    status: str
    status_color: str


class SummaryScoresResponse(BaseModel):
    executive_score: ExecutiveScoreResponse
    financial: ScoreDimensionResponse
    commercial: ScoreDimensionResponse
    operational: ScoreDimensionResponse


class SummaryKPIResponse(BaseModel):
    id: str
    title: str
    short_name: str
    display_name: str
    description: str
    subtitle: str
    value: float
    display_value: str
    formatted_value: str
    currency: str
    icon: str
    category: str
    trend: str
    trend_label: str
    trend_icon: str
    trend_color: str
    comparison: str
    health: dict[str, str]
    display_order: int


class SummarySeverityResponse(BaseModel):
    code: str
    label: str
    color: str
    icon: str


class SummaryImpactResponse(BaseModel):
    label: str
    display_value: str
    description: str


class SummaryAlertKPIResponse(BaseModel):
    name: str
    display_value: str


class SummaryAlertResponse(BaseModel):
    alert_id: str
    severity: SummarySeverityResponse
    priority: str
    category: str
    title: str
    subtitle: str
    message: str
    impact: SummaryImpactResponse | None
    kpi: SummaryAlertKPIResponse
    recommended_action: str
    details_available: bool
    icon: str
    color: str


class SummaryInsightResponse(BaseModel):
    title: str
    summary: str
    importance: str
    icon: str
    category: str
    display_order: int


class SummaryRecommendationResponse(BaseModel):
    recommendation_id: str
    title: str
    priority_label: str
    estimated_impact: str
    estimated_effort: str
    estimated_time: str
    category: str
    icon: str
    color: str
    action_button: str


class SummaryTrendAxisResponse(BaseModel):
    value: float
    display: str
    direction: str
    trend_icon: str
    trend_color: str
    trend_description: str
    icon: str
    color: str
    description: str


class SummaryTrendsResponse(BaseModel):
    monthly: SummaryTrendAxisResponse
    yearly: SummaryTrendAxisResponse


class SummaryTimelinePointResponse(BaseModel):
    label: str
    month: str
    year: int
    formatted_label: str
    formatted_date: str
    overall_score: float
    status: str
    status_color: str
    trend: str
    description: str
    trend_description: str


class SummaryTimelineResponse(BaseModel):
    points: list[SummaryTimelinePointResponse]


class SummaryRiskResponse(BaseModel):
    title: str
    summary: str
    probability: str


class SummaryHeroResponse(BaseModel):
    title: str
    score: int
    max_score: int
    progress: float
    grade: str
    status: str
    status_color: str
    status_icon: str
    variation: str
    comparison: str
    description: str
    last_updated: str


class SummaryHighlightResponse(BaseModel):
    icon: str
    title: str
    value: str
    subtitle: str
    color: str
    trend: str


class SummarySectionResponse(BaseModel):
    type: str
    title: str
    visible: bool
    count: int
    empty_message: str


class SummaryDashboardResponse(BaseModel):
    last_import: str | None
    last_pipeline: str
    pipeline_duration_ms: int | None
    summary_version: str
    refresh_interval_seconds: int
    data_quality: str


class GetSummaryResponse(BaseModel):
    summary_id: str
    company_id: str
    period_ref: str
    generated_at: str
    hero: SummaryHeroResponse
    highlights: list[SummaryHighlightResponse]
    sections: list[SummarySectionResponse]
    dashboard: SummaryDashboardResponse
    scores: SummaryScoresResponse
    kpis: list[SummaryKPIResponse]
    alerts: list[SummaryAlertResponse]
    insights: list[SummaryInsightResponse]
    recommendations: list[SummaryRecommendationResponse]
    trends: SummaryTrendsResponse
    next_risks: list[SummaryRiskResponse]
    timeline: SummaryTimelineResponse
