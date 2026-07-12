from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import MoneyFormatter, SeverityFormatter


def test_money_formatter_compact_brl() -> None:
    formatter = MoneyFormatter()
    assert formatter.format(1635916.85, "BRL") == "R$ 1,64 mi"
    assert formatter.format(186000, "BRL") == "R$ 186 mil"


def test_severity_formatter_translates_to_executive_labels() -> None:
    catalog = PresentationCatalog().load()
    formatter = SeverityFormatter(catalog)

    payload = formatter.format("MEDIUM")

    assert payload["code"] == "MEDIUM"
    assert payload["label"] == "Media"
    assert payload["color"] == "warning"
    assert payload["icon"] == "warning"
