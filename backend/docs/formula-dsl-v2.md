# Formula DSL v2

Date: 2026-07-12  
Status: Approved  
Reference: docs/semantic-layer/formula-dsl.v2.yaml

## 1) Purpose

Formula DSL v2 is the official and unique source of truth for KPI calculation in the platform.

Scope:
- Full formula coverage for all KPIs in the KPI Catalog.
- Compatibility with Canonical Data Model v2.
- Declarative formulas without hardcoded calculation logic in application code.

## 2) Structure

Top-level sections:
- metadata
- formulas

Each entry in formulas must contain exactly:
- formula_id
- name
- expression
- input_metrics
- output_type
- output_unit
- precision
- owner
- version
- effective_from

No extra fields are allowed in formula entries.

## 3) Versioning

Versioning rules:
- metadata.version identifies the catalog version.
- formula version is per-formula and incremented on semantic change.
- effective_from registers formula validity start date.

Recommended strategy:
- Keep formula_id stable for the same KPI semantic meaning.
- Increment version when expression, metrics, or unit semantics change.
- Create migration notes in changelog/release notes when formula behavior changes.

## 4) How To Add Formulas

1. Add or update KPI formula_id in kpi-catalog.v1.yaml.
2. Add formula entry in formula-dsl.v2.yaml using the exact required contract.
3. Ensure every input_metrics entry exists in canonical-data-model.v2.yaml.
4. Ensure output_unit matches KPI unit in kpi-catalog.v1.yaml.
5. Run unit tests for formula catalog and engine.

## 5) Validation

Validation checks implemented:
- Expression syntax is valid.
- Only whitelisted DSL functions are used.
- All input_metrics exist in canonical-data-model.v2.yaml.
- formula_id uniqueness and no duplicated formula names.
- output_unit compatibility with KPI Catalog unit.
- No circular dependencies in formula graph.
- Audit completeness:
  - every KPI has formula
  - every formula belongs to a KPI
  - no orphan formulas

## 6) Testing

Automated tests cover:
- YAML read and strict contract shape.
- Formula loading from official DSL v2.
- Compilation of all formula expressions.
- Semantic validation of all formulas and input metrics.
- Dependency graph validation (no cycle).
- KPI-to-formula audit with 100% coverage assertion.

Run focused suite:

```powershell
d:/Projetos/business-intelligence/.venv/Scripts/python.exe -m pytest tests/unit/kpi/test_formula_catalog_v2.py tests/unit/kpi/test_formula_engine.py tests/integration/test_formula_engine_api.py
```

Run complete suite:

```powershell
d:/Projetos/business-intelligence/.venv/Scripts/python.exe -m pytest
```
