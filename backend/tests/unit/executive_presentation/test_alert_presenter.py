from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import DateFormatter, MoneyFormatter, SeverityFormatter
from app.modules.executive_presentation.application.presenter import AlertPresenter


def test_alert_presenter_hides_technical_rule_language() -> None:
    catalog = PresentationCatalog().load()
    presenter = AlertPresenter(
        catalog=catalog,
        date_formatter=DateFormatter(catalog),
        severity_formatter=SeverityFormatter(catalog),
        money_formatter=MoneyFormatter(),
    )

    payload = presenter.present(
        {
            "alert_id": "rr_1",
            "rule_id": "r.fin01.net_revenue_below_target",
            "kpi_id": "FIN-01",
            "severity": "MEDIUM",
            "priority": "p1",
            "description": "Rule r.fin01...",
            "metric_value": 186000,
        },
        period_ref="2026-07",
        kpis={"FIN-01": {"value": 1635916.85, "title": "Receita Liquida"}},
    )

    assert payload["title"] == "Receita abaixo da meta"
    assert payload["message"] == "A receita liquida ficou abaixo da meta definida para este periodo."
    assert payload["severity"]["label"] == "Media"
    assert payload["priority"] == "P1"
    assert payload["kpi"]["name"] == "Receita Liquida"
    assert payload["impact"]["display_value"] == "R$ 186 mil"
    assert payload["icon"] == "payments"
    assert payload["color"] == "warning"
