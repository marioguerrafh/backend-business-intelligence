from app.modules.kpi.application.formula_dependency_resolver import FormulaDependencyResolver
from app.modules.kpi.application.formula_executor import FormulaExecutor
from app.modules.kpi.application.formula_parser import FormulaParser
from app.modules.kpi.application.formula_validator import FormulaValidator
from app.modules.kpi.application.ports.catalog_reader import CanonicalModelReader, FormulaCatalogReader
from app.modules.kpi.domain.formula_engine_entities import (
    FormulaAuditRecord,
    FormulaDefinition,
    FormulaEvaluationRequest,
    FormulaEvaluationResult,
)
from app.modules.kpi.domain.formula_engine_errors import FormulaValidationError


class FormulaEngineInternalAPI:
    """Internal API consumed by KPI engine use cases."""

    def __init__(
        self,
        formula_catalog: FormulaCatalogReader,
        canonical_model: CanonicalModelReader,
    ) -> None:
        self.formula_catalog = formula_catalog
        self.canonical_model = canonical_model
        self.parser = FormulaParser()
        self.validator = FormulaValidator()
        self.dependency_resolver = FormulaDependencyResolver()
        self.executor = FormulaExecutor()

    def evaluate_formula(self, request: FormulaEvaluationRequest) -> FormulaEvaluationResult:
        formulas = self.formula_catalog.load_formulas()
        canonical_fields = self.canonical_model.load_canonical_fields()

        definition = formulas.get(request.formula_id)
        if definition is None:
            raise FormulaValidationError(f"formula '{request.formula_id}' not found")

        relevant_formula_ids = self._dependency_closure(formulas, request.formula_id)
        relevant_formulas = {formula_id: formulas[formula_id] for formula_id in relevant_formula_ids}

        asts: dict[str, object] = {}
        for formula_id, formula in relevant_formulas.items():
            ast = self.parser.parse(formula.expression)
            self.validator.validate(formula, ast, canonical_fields, relevant_formulas.keys())
            asts[formula_id] = ast

        execution_order = self.dependency_resolver.resolve_order(relevant_formulas)
        resolved_metrics = dict(request.metrics)
        self._add_metric_aliases(resolved_metrics)
        trace_steps: list[str] = []

        for formula_id in execution_order:
            if formula_id == request.formula_id:
                value = self.executor.evaluate(asts[formula_id], resolved_metrics, trace_steps)
                rounded = round(value, definition.precision)
                audit = FormulaAuditRecord(
                    formula_id=definition.formula_id,
                    company_id=request.company_id,
                    period_ref=request.period_ref,
                    expression=definition.expression,
                    dependencies=self.dependency_resolver.dependencies_of(definition),
                    inputs_used={metric: resolved_metrics.get(metric) for metric in definition.input_metrics},
                    execution_steps=trace_steps,
                    result_value=rounded,
                    output_unit=definition.output_unit,
                )
                return FormulaEvaluationResult(
                    formula_id=definition.formula_id,
                    kpi_id=definition.kpi_id,
                    value=rounded,
                    unit=definition.output_unit,
                    precision=definition.precision,
                    audit=audit,
                )

            if formula_id in resolved_metrics:
                continue
            resolved_metrics[formula_id] = self.executor.evaluate(asts[formula_id], resolved_metrics, trace_steps)

        raise FormulaValidationError(f"formula '{request.formula_id}' could not be evaluated")

    def _dependency_closure(
        self,
        formulas: dict[str, FormulaDefinition],
        root_formula_id: str,
    ) -> list[str]:
        visited: set[str] = set()
        stack: list[str] = [root_formula_id]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            definition = formulas.get(current)
            if definition is None:
                raise FormulaValidationError(f"formula '{current}' referenced but not found")

            for dependency in self.dependency_resolver.dependencies_of(definition):
                stack.append(dependency)

        return sorted(visited)

    def _add_metric_aliases(self, metrics: dict[str, object]) -> None:
        alias_map: dict[str, object] = {}
        for key, value in metrics.items():
            if "." not in key:
                continue
            leaf = key.split(".")[-1]
            alias_map.setdefault(leaf, value)
        metrics.update(alias_map)
