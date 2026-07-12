from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import PercentFormatter, TrendFormatter


def test_trend_formatter_returns_icon_color_and_description() -> None:
    catalog = PresentationCatalog().load()
    formatter = TrendFormatter(catalog, PercentFormatter())

    direction = formatter.direction(8.0)

    assert direction == "up"
    assert formatter.label(8.0) == "+8,0%"
    assert formatter.icon(direction) == "trending_up"
    assert formatter.color(direction) == "success"
    assert formatter.description(direction) == "Crescimento em relacao ao mes anterior."
