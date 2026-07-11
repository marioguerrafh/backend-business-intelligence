from __future__ import annotations

from dataclasses import dataclass

from app.modules.rule.domain.errors import RuleConditionSyntaxError, RuleEvaluationError


_ALLOWED_FUNCTIONS = {
    "gt",
    "gte",
    "lt",
    "lte",
    "eq",
    "neq",
    "and",
    "or",
    "not",
    "consecutive_periods",
    "changed_by_percent",
    "trend_down",
}


@dataclass(slots=True, frozen=True)
class CallNode:
    fn: str
    args: tuple[object, ...]


def parse_condition(expression: str) -> CallNode:
    state = _ParserState(expression)
    node = state.parse_expr()
    state.skip_ws()
    if not state.is_eof():
        raise RuleConditionSyntaxError(f"unexpected token at index {state.idx}")
    if not isinstance(node, CallNode):
        raise RuleConditionSyntaxError("condition must be a function call")
    _validate_node(node)
    return node


def evaluate_condition(node: CallNode, *, metric_value: float, history: list[float], trace: list[str]) -> bool:
    result = _eval(node, metric_value=metric_value, history=history, trace=trace)
    return bool(result)


def _validate_node(node: object) -> None:
    if isinstance(node, CallNode):
        if node.fn not in _ALLOWED_FUNCTIONS:
            raise RuleConditionSyntaxError(f"unsupported operator '{node.fn}'")
        for arg in node.args:
            _validate_node(arg)


def _eval(node: object, *, metric_value: float, history: list[float], trace: list[str]) -> object:
    if isinstance(node, CallNode):
        values = [_eval(arg, metric_value=metric_value, history=history, trace=trace) for arg in node.args]
        fn = node.fn
        if fn == "gt":
            out = _num(values[0]) > _num(values[1])
        elif fn == "gte":
            out = _num(values[0]) >= _num(values[1])
        elif fn == "lt":
            out = _num(values[0]) < _num(values[1])
        elif fn == "lte":
            out = _num(values[0]) <= _num(values[1])
        elif fn == "eq":
            out = _num(values[0]) == _num(values[1])
        elif fn == "neq":
            out = _num(values[0]) != _num(values[1])
        elif fn == "and":
            out = all(bool(v) for v in values)
        elif fn == "or":
            out = any(bool(v) for v in values)
        elif fn == "not":
            out = not bool(values[0])
        elif fn == "consecutive_periods":
            count = int(_num(values[0]))
            out = len(history) >= count and all(v < 0 for v in history[-count:])
        elif fn == "changed_by_percent":
            threshold = _num(values[1])
            periods = _duration_to_points(str(values[2]))
            window = history[-periods:] if periods > 0 else history
            if len(window) < 2 or window[0] == 0:
                out = False
            else:
                pct = ((window[-1] - window[0]) / abs(window[0])) * 100.0
                out = pct <= threshold if threshold < 0 else pct >= threshold
        elif fn == "trend_down":
            if len(values) > 1:
                points = _duration_to_points(str(values[1]))
                series = history[-points:] if points > 0 else history
            else:
                series = history
            out = len(series) >= 2 and series[-1] < series[0]
        else:
            raise RuleEvaluationError(f"unsupported operator '{fn}'")
        trace.append(f"{fn}({values})={out}")
        return out

    if isinstance(node, (int, float)):
        return float(node)
    if isinstance(node, str):
        if node == "metric_value":
            return metric_value
        return node
    raise RuleEvaluationError("invalid condition AST")


def _num(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as exc:
            raise RuleEvaluationError(f"value '{value}' is not numeric") from exc
    raise RuleEvaluationError("non numeric operand")


def _duration_to_points(raw: str) -> int:
    token = raw.strip().lower()
    if token.endswith("d") or token.endswith("w") or token.endswith("m"):
        token = token[:-1]
    try:
        return int(token)
    except ValueError:
        return 0


class _ParserState:
    def __init__(self, source: str) -> None:
        self.source = source
        self.idx = 0

    def is_eof(self) -> bool:
        return self.idx >= len(self.source)

    def current(self) -> str:
        if self.is_eof():
            return ""
        return self.source[self.idx]

    def skip_ws(self) -> None:
        while not self.is_eof() and self.current().isspace():
            self.idx += 1

    def parse_expr(self) -> object:
        self.skip_ws()
        token = self.parse_token()
        self.skip_ws()
        if self.current() != "(":
            return token

        fn = str(token)
        self.idx += 1
        args: list[object] = []
        self.skip_ws()
        if self.current() == ")":
            self.idx += 1
            return CallNode(fn=fn, args=tuple(args))

        while True:
            args.append(self.parse_expr())
            self.skip_ws()
            if self.current() == ",":
                self.idx += 1
                self.skip_ws()
                continue
            if self.current() == ")":
                self.idx += 1
                break
            raise RuleConditionSyntaxError(f"expected ',' or ')' at index {self.idx}")
        return CallNode(fn=fn, args=tuple(args))

    def parse_token(self) -> object:
        self.skip_ws()
        start = self.idx
        while not self.is_eof() and self.current() not in ",()":
            self.idx += 1
        raw = self.source[start:self.idx].strip()
        if not raw:
            raise RuleConditionSyntaxError(f"expected token at index {self.idx}")

        if raw.lower() == "true":
            return 1.0
        if raw.lower() == "false":
            return 0.0
        try:
            return float(raw)
        except ValueError:
            return raw
