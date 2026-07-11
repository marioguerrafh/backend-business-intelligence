from collections.abc import Callable
from statistics import mean
from typing import Any

from app.modules.kpi.application.formula_parser import CallNode, IdentifierNode, NumberNode
from app.modules.kpi.domain.formula_engine_errors import FormulaExecutionError


class FormulaExecutor:
    def evaluate(
        self,
        ast: object,
        metrics: dict[str, Any],
        trace_steps: list[str],
    ) -> float:
        result = self._eval_node(ast, metrics, trace_steps)
        try:
            return float(result)
        except (TypeError, ValueError) as exc:
            raise FormulaExecutionError("formula result is not numeric") from exc

    def _eval_node(self, node: object, metrics: dict[str, Any], trace_steps: list[str]) -> Any:
        if isinstance(node, NumberNode):
            return node.value
        if isinstance(node, IdentifierNode):
            if node.name not in metrics:
                raise FormulaExecutionError(f"missing metric '{node.name}' in evaluation context")
            value = metrics[node.name]
            trace_steps.append(f"identifier:{node.name}={value}")
            return value
        if isinstance(node, CallNode):
            values = [self._eval_node(arg, metrics, trace_steps) for arg in node.args]
            fn = self._get_function(node.function)
            result = fn(values)
            trace_steps.append(f"call:{node.function}({values})={result}")
            return result
        raise FormulaExecutionError("invalid execution AST node")

    def _get_function(self, name: str) -> Callable[[list[Any]], Any]:
        table: dict[str, Callable[[list[Any]], Any]] = {
            "add": lambda v: self._numeric(v[0]) + self._numeric(v[1]),
            "sub": lambda v: self._numeric(v[0]) - self._numeric(v[1]),
            "mul": lambda v: self._numeric(v[0]) * self._numeric(v[1]),
            "div": self._div,
            "abs": lambda v: abs(self._numeric(v[0])),
            "round": self._round,
            "sum": self._sum,
            "avg": self._avg,
            "min": lambda v: min(self._expand_values(v)),
            "max": lambda v: max(self._expand_values(v)),
            "count": lambda v: len(self._expand_values(v)),
            "count_distinct": lambda v: len(set(self._expand_values(v))),
            "weighted_avg": self._weighted_avg,
            "rolling_sum": self._sum,
            "rolling_avg": self._avg,
            "period_over_period": lambda v: self._numeric(v[0]) - self._numeric(v[1]),
            "trend_slope": self._trend_slope,
            "if": self._if,
            "coalesce": self._coalesce,
            "clamp": self._clamp,
        }
        if name not in table:
            raise FormulaExecutionError(f"unsupported function '{name}'")
        return table[name]

    def _numeric(self, value: Any) -> float:
        if isinstance(value, list):
            raise FormulaExecutionError("list value received where scalar expected")
        return float(value)

    def _expand_values(self, values: list[Any]) -> list[float]:
        expanded: list[float] = []
        for value in values:
            if isinstance(value, list):
                expanded.extend(float(item) for item in value)
            else:
                expanded.append(float(value))
        return expanded

    def _sum(self, values: list[Any]) -> float:
        return float(sum(self._expand_values(values)))

    def _avg(self, values: list[Any]) -> float:
        expanded = self._expand_values(values)
        if not expanded:
            return 0.0
        return float(mean(expanded))

    def _div(self, values: list[Any]) -> float:
        denominator = self._numeric(values[1])
        if denominator == 0:
            raise FormulaExecutionError("division by zero")
        return self._numeric(values[0]) / denominator

    def _round(self, values: list[Any]) -> float:
        if len(values) == 1:
            return float(round(self._numeric(values[0])))
        return float(round(self._numeric(values[0]), int(self._numeric(values[1]))))

    def _weighted_avg(self, values: list[Any]) -> float:
        if len(values) != 2:
            raise FormulaExecutionError("weighted_avg requires values and weights")
        metrics = values[0]
        weights = values[1]
        if not isinstance(metrics, list) or not isinstance(weights, list):
            raise FormulaExecutionError("weighted_avg requires list inputs")
        if len(metrics) != len(weights):
            raise FormulaExecutionError("weighted_avg requires equal sized lists")
        weight_total = sum(float(weight) for weight in weights)
        if weight_total == 0:
            raise FormulaExecutionError("weighted_avg weight total cannot be zero")
        total = sum(float(metric) * float(weight) for metric, weight in zip(metrics, weights, strict=False))
        return float(total / weight_total)

    def _trend_slope(self, values: list[Any]) -> float:
        if not values:
            return 0.0
        series = values[0]
        if not isinstance(series, list) or len(series) < 2:
            return 0.0
        return float(series[-1]) - float(series[0])

    def _if(self, values: list[Any]) -> Any:
        if len(values) != 3:
            raise FormulaExecutionError("if function requires condition, then, else")
        condition = values[0]
        return values[1] if bool(condition) else values[2]

    def _coalesce(self, values: list[Any]) -> Any:
        for value in values:
            if value is not None:
                return value
        return 0.0

    def _clamp(self, values: list[Any]) -> float:
        if len(values) != 3:
            raise FormulaExecutionError("clamp requires value, min, max")
        current = self._numeric(values[0])
        min_value = self._numeric(values[1])
        max_value = self._numeric(values[2])
        if min_value > max_value:
            raise FormulaExecutionError("clamp min cannot be greater than max")
        return max(min_value, min(max_value, current))
