from __future__ import annotations

from dataclasses import dataclass

from app.modules.kpi.application.formula_dependency_resolver import FormulaDependencyResolver
from app.modules.kpi.application.formula_parser import FormulaParser
from app.modules.kpi.application.formula_validator import FormulaValidator
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition
from app.modules.kpi.domain.formula_engine_errors import FormulaValidationError


@dataclass(slots=True, frozen=True)
class FormulaCatalogValidationResult:
    formula_count: int
    kpi_count: int
    coverage_percent: float


class FormulaCatalogValidator:
    def __init__(self) -> None:
        self.parser = FormulaParser()
        self.validator = FormulaValidator()
        self.dependency_resolver = FormulaDependencyResolver()

    def validate(
        self,
        *,
        formulas: dict[str, FormulaDefinition],
        canonical_fields: set[str],
        kpi_formula_map: dict[str, str],
        kpi_unit_map: dict[str, str],
    ) -> FormulaCatalogValidationResult:
        if not formulas:
            raise FormulaValidationError("formula catalog is empty")

        self._validate_no_duplicate_formula_names(formulas)
        self._validate_compilation_and_semantics(formulas, canonical_fields)
        self._validate_no_circular_dependencies(formulas)
        self._validate_unit_compatibility(formulas, kpi_formula_map, kpi_unit_map)
        self._validate_kpi_audit(formulas, kpi_formula_map)

        formula_count = len(formulas)
        kpi_count = len(kpi_formula_map)
        coverage = (formula_count / kpi_count) * 100 if kpi_count else 0.0
        return FormulaCatalogValidationResult(
            formula_count=formula_count,
            kpi_count=kpi_count,
            coverage_percent=round(coverage, 2),
        )

    def _validate_no_duplicate_formula_names(self, formulas: dict[str, FormulaDefinition]) -> None:
        seen_names: set[str] = set()
        for formula in formulas.values():
            normalized = formula.name.strip().lower()
            if normalized in seen_names:
                raise FormulaValidationError(
                    f"duplicate formula name detected: {formula.name}"
                )
            seen_names.add(normalized)

    def _validate_compilation_and_semantics(
        self,
        formulas: dict[str, FormulaDefinition],
        canonical_fields: set[str],
    ) -> None:
        formula_ids = formulas.keys()
        for definition in formulas.values():
            ast = self.parser.parse(definition.expression)
            self.validator.validate(definition, ast, canonical_fields, formula_ids)

    def _validate_no_circular_dependencies(self, formulas: dict[str, FormulaDefinition]) -> None:
        self.dependency_resolver.resolve_order(formulas)

    def _validate_unit_compatibility(
        self,
        formulas: dict[str, FormulaDefinition],
        kpi_formula_map: dict[str, str],
        kpi_unit_map: dict[str, str],
    ) -> None:
        formula_to_kpi = {formula_id: kpi_id for kpi_id, formula_id in kpi_formula_map.items()}
        for formula_id, definition in formulas.items():
            kpi_id = formula_to_kpi.get(formula_id)
            if not kpi_id:
                continue
            expected_unit = (kpi_unit_map.get(kpi_id) or "").strip().upper()
            current_unit = (definition.output_unit or "").strip().upper()
            if expected_unit and current_unit != expected_unit:
                raise FormulaValidationError(
                    f"formula {formula_id} output_unit '{definition.output_unit}' is not compatible with KPI {kpi_id} unit '{kpi_unit_map[kpi_id]}'"
                )

    def _validate_kpi_audit(
        self,
        formulas: dict[str, FormulaDefinition],
        kpi_formula_map: dict[str, str],
    ) -> None:
        kpi_formula_ids = set(kpi_formula_map.values())
        formula_ids = set(formulas.keys())

        orphan_formulas = sorted(formula_ids - kpi_formula_ids)
        missing_kpis = sorted(kpi_id for kpi_id, formula_id in kpi_formula_map.items() if formula_id not in formula_ids)

        if orphan_formulas:
            raise FormulaValidationError(f"orphan formulas without KPI mapping: {', '.join(orphan_formulas)}")
        if missing_kpis:
            raise FormulaValidationError(f"KPIs without formula: {', '.join(missing_kpis)}")
