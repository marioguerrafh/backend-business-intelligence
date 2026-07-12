from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.presenter import ExecutivePresentationMapper


def test_presentation_mapper_transforms_summary_payload_end_to_end() -> None:
    mapper = ExecutivePresentationMapper(catalog_reader=PresentationCatalog())

    payload = mapper.present(
        {
            "summary_id": "sum_1",
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "generated_at": "2026-07-12T10:00:00Z",
            "scores": {"overall": 80.5, "financial": 81, "commercial": 79, "operational": 78},
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
                    "description": "Rule r.fin01...",
                    "metric_value": 186000,
                }
            ],
            "insights": [
                {"insight_id": "in_1", "type": "trend", "statement": "O faturamento permaneceu estavel."}
            ],
            "recommendations": [
                {
                    "recommendation_id": "rec_1",
                    "title": "Revisar politica comercial",
                    "rank": 0.9,
                    "expected_impact": {"value": 12000, "unit": "BRL"},
                }
            ],
            "trends": {"today_vs_last_month": 0.12, "today_vs_last_year": 0.185},
            "next_risks": [{"title": "Caixa pressionado", "description": "Exposicao de liquidez", "probability": 0.8}],
            "timeline": {
                "points": [
                    {
                        "snapshot_date": "2026-07-10",
                        "overall_score": 80,
                        "financial_score": 81,
                        "commercial_score": 79,
                        "operational_score": 78,
                    }
                ]
            },
        }
    )

    assert payload["kpis"][0]["title"] == "Receita Liquida"
    assert payload["kpis"][0]["health"]["label"] == "Saudavel"
    assert payload["alerts"][0]["message"] == "A receita liquida ficou abaixo da meta definida para este periodo."
    assert payload["insights"][0]["title"] == "Receita estavel"
    assert payload["hero"]["title"] == "Saude da Empresa"
    assert payload["hero"]["last_updated"] == "12/07/2026 10:00"
    assert payload["hero"]["progress"] == 0.805
    assert len(payload["highlights"]) == 4
    assert payload["highlights"][0]["title"] == "Receita"
    assert payload["highlights"][0]["value"] == "R$ 1,64 mi"
    assert payload["sections"][0]["type"] == "hero"
    assert payload["sections"][0]["visible"] is True
    assert payload["dashboard"]["summary_version"] == "3.1"
    assert payload["scores"]["executive_score"]["overall"] == 80.5
    assert payload["trends"]["monthly"]["display"] == "+12,0%"
    assert payload["trends"]["monthly"]["trend_icon"] == "trending_up"
    assert payload["recommendations"][0]["action_button"] == "Ver plano de acao"
    assert payload["recommendations"][0]["estimated_impact"] == "R$ 12 mil"
    assert payload["timeline"]["points"][0]["formatted_label"] == "Jul/26"
    assert payload["timeline"]["points"][0]["description"]
    assert payload["timeline"]["points"][0]["formatted_date"] == "10/07/2026"
