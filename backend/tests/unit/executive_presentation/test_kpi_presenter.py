from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import DateFormatter, MoneyFormatter, PercentFormatter, QuantityFormatter
from app.modules.executive_presentation.application.presenter import KpiPresenter


def test_kpi_presenter_returns_executive_payload() -> None:
    catalog = PresentationCatalog().load()
    presenter = KpiPresenter(
        catalog=catalog,
        date_formatter=DateFormatter(catalog),
        money_formatter=MoneyFormatter(),
        percent_formatter=PercentFormatter(),
        quantity_formatter=QuantityFormatter(),
    )

    payload = presenter.present(
        {
            "kpi_id": "FIN-01",
            "name": "receita_liquida",
            "value": 1635916.85,
            "unit": "BRL",
            "trend": "up",
            "health": "green",
        },
        period_ref="2026-07",
        display_order=1,
    )

    assert payload["id"] == "FIN-01"
    assert payload["title"] == "Receita Liquida"
    assert payload["short_name"] == "Receita"
    assert payload["display_name"] == "Receita Liquida"
    assert payload["description"]
    assert payload["subtitle"] == "Julho de 2026"
    assert payload["display_value"] == "R$ 1,64 mi"
    assert payload["formatted_value"] == "R$ 1,64 mi"
    assert payload["icon"] == "payments"
    assert payload["category"] == "Financeiro"
    assert payload["trend_icon"] == "trending_up"
    assert payload["comparison"] == "em relacao ao mes anterior"
