from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.presenter import ExecutivePresentationMapper


def test_mapper_builds_executive_hero_block() -> None:
    mapper = ExecutivePresentationMapper(catalog_reader=PresentationCatalog())

    payload = mapper.present(
        {
            "summary_id": "sum_1",
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "generated_at": "2026-07-12T11:42:00Z",
            "scores": {"overall": 96, "financial": 90, "commercial": 88, "operational": 91},
            "kpis": [],
            "alerts": [],
            "insights": [],
            "recommendations": [],
            "trends": {"today_vs_last_month": 0.03, "today_vs_last_year": 0.1},
            "next_risks": [],
            "timeline": {"points": []},
        }
    )

    assert payload["hero"]["title"] == "Saude da Empresa"
    assert payload["hero"]["score"] == 96
    assert payload["hero"]["max_score"] == 100
    assert payload["hero"]["progress"] == 0.96
    assert payload["hero"]["grade"] == "A+"
    assert payload["hero"]["status"] == "Excelente"
    assert payload["hero"]["status_icon"] == "workspace_premium"
    assert payload["hero"]["last_updated"] == "12/07/2026 11:42"
