from collections.abc import Iterable

from app.modules.kpi.application.formula_parser import CallNode, IdentifierNode, NumberNode
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition
from app.modules.kpi.domain.formula_engine_errors import FormulaValidationError


class FormulaValidator:
    allowed_functions = {
        "add",
        "sub",
        "mul",
        "div",
        "abs",
        "round",
        "sum",
        "avg",
        "min",
        "max",
        "count",
        "count_distinct",
        "weighted_avg",
        "rolling_sum",
        "rolling_avg",
        "period_over_period",
        "trend_slope",
        "if",
        "coalesce",
        "clamp",
    }

    def validate(
        self,
        definition: FormulaDefinition,
        ast: object,
        canonical_fields: set[str],
        formula_ids: Iterable[str],
    ) -> None:
        known_formula_ids = set(formula_ids)
        for metric in definition.input_metrics:
            if metric in known_formula_ids:
                continue
            if metric.startswith("formula:") and metric.removeprefix("formula:") in known_formula_ids:
                continue
            if metric.startswith("kpi_score."):
                continue
            if metric not in canonical_fields:
                raise FormulaValidationError(
                    f"formula {definition.formula_id} references unknown metric '{metric}'"
                )

        self._validate_ast(ast)

        allowed_identifiers = self._build_allowed_identifiers(definition, known_formula_ids)
        used_identifiers = self._collect_identifiers(ast)
        for identifier in used_identifiers:
            if identifier not in allowed_identifiers:
                raise FormulaValidationError(
                    f"formula {definition.formula_id} uses undeclared identifier '{identifier}'"
                )

    def _build_allowed_identifiers(
        self,
        definition: FormulaDefinition,
        known_formula_ids: set[str],
    ) -> set[str]:
        allowed: set[str] = set()
        for metric in definition.input_metrics:
            allowed.add(metric)
            if "." in metric:
                allowed.add(metric.split(".")[-1])
            if metric.startswith("formula:"):
                allowed.add(metric.removeprefix("formula:"))
            if metric.startswith("formula."):
                allowed.add(metric.removeprefix("formula."))
        allowed.update(known_formula_ids)
        return allowed

    def _collect_identifiers(self, node: object) -> set[str]:
        identifiers: set[str] = set()
        self._walk_identifiers(node, identifiers)
        return identifiers

    def _walk_identifiers(self, node: object, identifiers: set[str]) -> None:
        if isinstance(node, IdentifierNode):
            identifiers.add(node.name)
            return
        if isinstance(node, CallNode):
            for arg in node.args:
                self._walk_identifiers(arg, identifiers)
            return
        if isinstance(node, NumberNode):
            return

    def _validate_ast(self, node: object) -> None:
        if isinstance(node, NumberNode):
            return
        if isinstance(node, IdentifierNode):
            return
        if isinstance(node, CallNode):
            if node.function not in self.allowed_functions:
                raise FormulaValidationError(f"function '{node.function}' is not allowed")
            for arg in node.args:
                self._validate_ast(arg)
            return
        raise FormulaValidationError("invalid AST node")
