from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.presenter import InsightPresenter


def test_insight_presenter_returns_executive_language() -> None:
    catalog = PresentationCatalog().load()
    presenter = InsightPresenter(catalog=catalog)

    payload = presenter.present(
        {
            "insight_id": "in_1",
            "type": "trend",
            "statement": "O faturamento permaneceu estavel em relacao ao periodo anterior.",
        }
    )

    assert payload["title"] == "Receita estavel"
    assert payload["importance"] == "low"
    assert payload["icon"] == "analytics"
    assert payload["category"] == "Financeiro"
