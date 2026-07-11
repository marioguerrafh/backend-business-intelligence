from app.modules.executive_score.application.score_calculator import ExecutiveScoreCalculator
from app.modules.executive_score.domain.entities import ScoreInputs


def test_executive_score_calculator_applies_weights_and_bounds() -> None:
    calc = ExecutiveScoreCalculator()

    financial, commercial, operational, inventory, executive = calc.calculate(
        ScoreInputs(
            financial_values=(80.0, 90.0),
            commercial_values=(70.0,),
            operational_values=(60.0,),
            inventory_values=(50.0,),
            rule_penalty=5.0,
            recommendation_bonus=2.0,
        )
    )

    assert financial == 85.0
    assert commercial == 70.0
    assert operational == 60.0
    assert inventory == 50.0
    assert 0.0 <= executive <= 100.0


def test_executive_score_calculator_defaults_when_inputs_missing() -> None:
    calc = ExecutiveScoreCalculator()

    financial, commercial, operational, inventory, executive = calc.calculate(
        ScoreInputs(
            financial_values=(),
            commercial_values=(),
            operational_values=(),
            inventory_values=(),
            rule_penalty=0.0,
            recommendation_bonus=0.0,
        )
    )

    assert financial == 70.0
    assert commercial == 70.0
    assert operational == 70.0
    assert inventory == 70.0
    assert executive == 70.0
