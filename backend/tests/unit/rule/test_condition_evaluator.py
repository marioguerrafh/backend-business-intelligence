from app.modules.rule.application.condition_evaluator import evaluate_condition, parse_condition


def test_rule_condition_parses_and_evaluates_basic_comparison() -> None:
    node = parse_condition("gt(metric_value, 5)")
    trace: list[str] = []
    result = evaluate_condition(node, metric_value=8.0, history=[2.0, 4.0, 8.0], trace=trace)

    assert result is True
    assert any("gt" in step for step in trace)


def test_rule_condition_evaluates_temporal_changed_by_percent() -> None:
    node = parse_condition("changed_by_percent(metric_value, -10, 3d)")
    trace: list[str] = []
    result = evaluate_condition(node, metric_value=80.0, history=[100.0, 90.0, 80.0], trace=trace)

    assert result is True


def test_rule_condition_evaluates_consecutive_periods_negative_history() -> None:
    node = parse_condition("and(lt(metric_value,0), consecutive_periods(3, day))")
    trace: list[str] = []
    result = evaluate_condition(node, metric_value=-2.0, history=[-1.0, -3.0, -2.0], trace=trace)

    assert result is True
