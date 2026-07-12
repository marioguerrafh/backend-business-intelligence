from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import DateFormatter


def test_timeline_label_formatter() -> None:
    formatter = DateFormatter(PresentationCatalog().load())

    month, year, label = formatter.timeline_label("2026-07-10")

    assert month == "Jul"
    assert year == 2026
    assert label == "Jul/26"
