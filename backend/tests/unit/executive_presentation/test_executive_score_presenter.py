from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import PercentFormatter, ScoreFormatter
from app.modules.executive_presentation.application.presenter import ExecutiveScorePresenter


def test_executive_score_presenter_builds_status_block() -> None:
    catalog = PresentationCatalog().load()
    presenter = ExecutiveScorePresenter(
        catalog=catalog,
        score_formatter=ScoreFormatter(catalog),
        percent_formatter=PercentFormatter(),
    )

    payload = presenter.present(
        {"overall": 80.5},
        {"today_vs_last_month": 0.03},
    )

    assert payload["overall"] == 80.5
    assert payload["display"] == "80"
    assert payload["status"] in {"Excelente", "Muito Boa", "Boa", "Atencao", "Critica", "Grave"}
    assert payload["status_description"]
    assert payload["icon"]
    assert payload["color"]
    assert payload["status_color"]
    assert payload["variation"].startswith("+")
    assert payload["comparison"] == "em relacao ao mes anterior"
