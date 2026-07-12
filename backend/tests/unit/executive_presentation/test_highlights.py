from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.presenter import ExecutivePresentationMapper


def test_mapper_builds_highlights_block() -> None:
    mapper = ExecutivePresentationMapper(catalog_reader=PresentationCatalog())

    payload = mapper.present(
        {
            "summary_id": "sum_1",
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "generated_at": "2026-07-12T10:00:00Z",
            "scores": {"overall": 80, "financial": 80, "commercial": 80, "operational": 80},
            "kpis": [
                {
                    "kpi_id": "FIN-01",
                    "name": "receita_liquida",
                    "value": 1635916.85,
                    "unit": "BRL",
                    "trend": "up",
                    "health": "green",
                }
            ],
            "alerts": [
                {
                    "alert_id": "rr_1",
                    "rule_id": "r.fin01.net_revenue_below_target",
                    "kpi_id": "FIN-01",
                    "severity": "MEDIUM",
                    "priority": "p1",
                    "metric_value": 186000,
                },
                {
                    "alert_id": "rr_2",
                    "rule_id": "r.fin01.net_revenue_below_target",
                    "kpi_id": "FIN-01",
                    "severity": "MEDIUM",
                    "priority": "p1",
                    "metric_value": 100000,
                },
            ],
            "insights": [],
            "recommendations": [],
            "trends": {"today_vs_last_month": 0.08, "today_vs_last_year": 0.12},
            "next_risks": [],
            "timeline": {"points": []},
        }
    )

    assert len(payload["highlights"]) == 4
    assert payload["highlights"][0]["title"] == "Receita"
    assert payload["highlights"][0]["value"] == "R$ 1,64 mi"
    assert payload["highlights"][1]["title"] == "Alertas ativos"
    assert payload["highlights"][1]["value"] == "2 alertas ativos"
    assert payload["highlights"][2]["title"] == "Tendencia de receita"
    assert payload["highlights"][3]["title"] == "Executive Score"
