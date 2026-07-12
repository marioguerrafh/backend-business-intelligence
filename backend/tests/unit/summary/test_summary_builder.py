from datetime import datetime, timezone

from app.modules.summary.application.ports.repository import SummarySourcePayload
from app.modules.summary.application.summary_builder import SummaryBuilder


def test_summary_builder_maps_payload_and_computes_trends() -> None:
    source = SummarySourcePayload(
        company_id="cmp_acme",
        period_ref="2026-07",
        generated_at=datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
        scores={"overall": 80.0, "financial": 81.0, "commercial": 79.0, "operational": 78.0},
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
        alerts=(
            {
                "alert_id": "r1",
                "severity": "high",
                "priority": "p1",
                "title": "Receita em queda",
                "description": "queda de 7%",
            },
        ),
        insights=(
            {
                "insight_id": "i1",
                "type": "trend",
                "statement": "margem melhorou",
                "evidence": {"delta": 1.5},
            },
        ),
        recommendations=(
            {
                "recommendation_id": "rec1",
                "title": "revisar pricing",
                "rank": 0.91,
                "expected_impact": {"value": 20000, "unit": "BRL"},
                "owner_role": "cfo",
                "sla_target": "7d",
            },
        ),
        timeline_points=(
            {"snapshot_date": "2026-07-10", "overall_score": 80, "financial_score": 81, "commercial_score": 79, "operational_score": 78},
            {"snapshot_date": "2026-07-09", "overall_score": 77, "financial_score": 78, "commercial_score": 76, "operational_score": 75},
            {"snapshot_date": "2026-06-10", "overall_score": 70, "financial_score": 71, "commercial_score": 69, "operational_score": 68},
            {"snapshot_date": "2025-07-10", "overall_score": 60, "financial_score": 61, "commercial_score": 59, "operational_score": 58},
        ),
        next_risks=({"risk_code": "cash.low", "probability": 0.8},),
        dashboard={
            "last_import": "2026-07-10T11:58:00+00:00",
            "last_pipeline": "completed",
            "pipeline_duration_ms": 3400,
            "summary_version": "3.1",
            "refresh_interval_seconds": 300,
            "data_quality": "excellent",
        },
    )

    aggregate = SummaryBuilder().build(summary_id="sum_1", source=source)

    assert aggregate.company_id == "cmp_acme"
    assert aggregate.trends.today_vs_yesterday == 3.0
    assert aggregate.trends.today_vs_last_month == 10.0
    assert aggregate.trends.today_vs_last_year == 20.0
    assert aggregate.kpis[0].name == "Margem"
    assert aggregate.recommendations[0].expected_impact["unit"] == "BRL"
