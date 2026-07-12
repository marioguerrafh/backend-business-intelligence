from __future__ import annotations

from pathlib import Path

import yaml

from app.modules.kpi.application.formula_catalog_validator import FormulaCatalogValidator
from app.modules.kpi.application.formula_dependency_resolver import FormulaDependencyResolver
from app.modules.kpi.application.formula_parser import FormulaParser
from app.modules.kpi.application.formula_validator import FormulaValidator
from app.modules.kpi.infrastructure.formula_catalog_yaml import YamlCanonicalModelReader, YamlFormulaCatalogReader
from app.modules.kpi.infrastructure.kpi_catalog_yaml import YamlKpiCatalogReader


REQUIRED_FORMULA_KEYS = {
    "formula_id",
    "name",
    "expression",
    "input_metrics",
    "output_type",
    "output_unit",
    "precision",
    "owner",
    "version",
    "effective_from",
}


def _kpi_maps() -> tuple[dict[str, str], dict[str, str]]:
    kpis = YamlKpiCatalogReader().load_kpis()
    formula_map = {kpi_id: str(item["formula_id"]) for kpi_id, item in kpis.items()}
    unit_map = {kpi_id: str(item["unit"]) for kpi_id, item in kpis.items()}
    return formula_map, unit_map


def test_formula_dsl_v2_yaml_contract_and_count() -> None:
    path = Path("docs/semantic-layer/formula-dsl.v2.yaml")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert "formula_examples" not in payload
    formulas = payload.get("formulas")
    assert isinstance(formulas, list)
    assert len(formulas) == 49

    for item in formulas:
        assert isinstance(item, dict)
        assert set(item.keys()) == REQUIRED_FORMULA_KEYS


def test_formula_dsl_v2_reader_loads_all_formulas() -> None:
    formulas = YamlFormulaCatalogReader().load_formulas()

    assert len(formulas) == 49
    assert "revenue.net" in formulas
    assert "executive.business_health_index" in formulas


def test_formula_dsl_v2_all_expressions_compile() -> None:
    parser = FormulaParser()
    formulas = YamlFormulaCatalogReader().load_formulas()

    for definition in formulas.values():
        parser.parse(definition.expression)


def test_formula_dsl_v2_input_metrics_exist_and_semantics_are_valid() -> None:
    formulas = YamlFormulaCatalogReader().load_formulas()
    canonical_fields = YamlCanonicalModelReader().load_canonical_fields()
    validator = FormulaValidator()
    parser = FormulaParser()

    for definition in formulas.values():
        for metric in definition.input_metrics:
            assert metric in canonical_fields
        ast = parser.parse(definition.expression)
        validator.validate(definition, ast, canonical_fields, formulas.keys())


def test_formula_dsl_v2_has_no_circular_dependencies() -> None:
    formulas = YamlFormulaCatalogReader().load_formulas()
    resolver = FormulaDependencyResolver()

    order = resolver.resolve_order(formulas)

    assert len(order) == len(formulas)


def test_formula_dsl_v2_audit_full_coverage_and_no_orphans() -> None:
    formulas = YamlFormulaCatalogReader().load_formulas()
    canonical_fields = YamlCanonicalModelReader().load_canonical_fields()
    kpi_formula_map, kpi_unit_map = _kpi_maps()

    result = FormulaCatalogValidator().validate(
        formulas=formulas,
        canonical_fields=canonical_fields,
        kpi_formula_map=kpi_formula_map,
        kpi_unit_map=kpi_unit_map,
    )

    assert result.formula_count == 49
    assert result.kpi_count == 49
    assert result.coverage_percent == 100.0
