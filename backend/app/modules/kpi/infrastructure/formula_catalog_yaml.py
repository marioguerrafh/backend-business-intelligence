from pathlib import Path
from typing import Any

import yaml

from app.modules.kpi.application.ports.catalog_reader import CanonicalModelReader, FormulaCatalogReader
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition
from app.modules.kpi.domain.formula_engine_errors import FormulaValidationError


class YamlFormulaCatalogReader(FormulaCatalogReader):
    def __init__(self, formula_dsl_path: Path | None = None) -> None:
        self.formula_dsl_path = formula_dsl_path or self._default_path("formula-dsl.v2.yaml")

    def load_formulas(self) -> dict[str, FormulaDefinition]:
        payload = self._read_yaml(self.formula_dsl_path)
        formula_items = payload.get("formulas")
        if not isinstance(formula_items, list) or not formula_items:
            raise FormulaValidationError("formula catalog is empty")

        if "formula_examples" in payload:
            raise FormulaValidationError("formula_examples is not supported in formula DSL v2")

        formula_to_kpi = self._formula_to_kpi_index()
        required_keys = {
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

        formulas: dict[str, FormulaDefinition] = {}
        for index, item in enumerate(formula_items):
            if not isinstance(item, dict):
                raise FormulaValidationError(f"formula entry at index {index} must be an object")

            keys = set(item.keys())
            if keys != required_keys:
                missing = sorted(required_keys - keys)
                extras = sorted(keys - required_keys)
                detail: list[str] = []
                if missing:
                    detail.append(f"missing fields: {', '.join(missing)}")
                if extras:
                    detail.append(f"extra fields: {', '.join(extras)}")
                raise FormulaValidationError(
                    f"formula entry at index {index} violates required contract ({'; '.join(detail)})"
                )

            formula_id = str(item["formula_id"]).strip()
            if not formula_id:
                raise FormulaValidationError(f"formula entry at index {index} has empty formula_id")
            if formula_id in formulas:
                raise FormulaValidationError(f"duplicate formula_id: {formula_id}")

            kpi_id = formula_to_kpi.get(formula_id)
            if not kpi_id:
                raise FormulaValidationError(
                    f"formula {formula_id} has no linked KPI in kpi-catalog.v1.yaml"
                )

            metrics = item.get("input_metrics")
            if not isinstance(metrics, list):
                raise FormulaValidationError(
                    f"formula {formula_id} input_metrics must be a list"
                )

            formulas[formula_id] = FormulaDefinition(
                formula_id=formula_id,
                kpi_id=kpi_id,
                name=str(item["name"]),
                expression=str(item["expression"]),
                input_metrics=tuple(str(metric) for metric in metrics),
                output_type=str(item["output_type"]),
                output_unit=str(item["output_unit"]),
                precision=int(item["precision"]),
                owner=str(item["owner"]),
                version=int(item["version"]),
                effective_from=str(item["effective_from"]),
            )

        expected_formula_ids = set(formula_to_kpi.keys())
        missing_kpis = sorted(
            kpi_id for formula_id, kpi_id in formula_to_kpi.items() if formula_id not in formulas
        )
        orphan_formulas = sorted(formula_id for formula_id in formulas if formula_id not in expected_formula_ids)
        if missing_kpis:
            raise FormulaValidationError(
                f"kpi catalog contains KPIs without formula in formula-dsl.v2.yaml: {', '.join(missing_kpis)}"
            )
        if orphan_formulas:
            raise FormulaValidationError(
                f"formula-dsl.v2.yaml contains formulas without KPI mapping: {', '.join(orphan_formulas)}"
            )

        return formulas

    def _formula_to_kpi_index(self) -> dict[str, str]:
        payload = self._read_yaml(self._default_path("kpi-catalog.v1.yaml"))
        kpis = payload.get("kpis") or {}
        if not isinstance(kpis, dict):
            raise FormulaValidationError("kpi catalog has invalid format")
        index: dict[str, str] = {}
        for kpi_id, item in kpis.items():
            if not isinstance(item, dict):
                continue
            formula_id = str(item.get("formula_id") or "").strip()
            if not formula_id:
                continue
            index[formula_id] = str(item.get("id") or kpi_id)
        return index

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as fp:
                payload = yaml.safe_load(fp) or {}
        except FileNotFoundError as exc:
            raise FormulaValidationError(f"yaml file not found: {path}") from exc

        if not isinstance(payload, dict):
            raise FormulaValidationError(f"yaml root must be an object: {path}")
        return payload

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename

    def _module_local_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parent / filename


class YamlCanonicalModelReader(CanonicalModelReader):
    def __init__(self, canonical_model_path: Path | None = None) -> None:
        self.canonical_model_path = canonical_model_path or self._default_path("canonical-data-model.v2.yaml")

    def load_canonical_fields(self) -> set[str]:
        try:
            with self.canonical_model_path.open("r", encoding="utf-8") as fp:
                payload = yaml.safe_load(fp) or {}
        except FileNotFoundError as exc:
            fallback_path = self._module_local_path("canonical-data-model.v2.yaml")
            if fallback_path != self.canonical_model_path and fallback_path.exists():
                with fallback_path.open("r", encoding="utf-8") as fp:
                    payload = yaml.safe_load(fp) or {}
            else:
                raise FormulaValidationError(
                    f"canonical model file not found: {self.canonical_model_path}"
                ) from exc

        fields: set[str] = set()
        for fact_name, fact_data in (payload.get("canonical_facts") or {}).items():
            for measure in fact_data.get("measures", []):
                fields.add(f"{fact_name}.{measure}")
            for field_data in fact_data.get("fields", []):
                if isinstance(field_data, dict) and "name" in field_data:
                    fields.add(f"{fact_name}.{field_data['name']}")

        for dim_name, dim_data in (payload.get("core_dimensions") or {}).items():
            for attr in dim_data.get("attributes", []):
                fields.add(f"{dim_name}.{attr}")

        if not fields:
            raise FormulaValidationError("canonical model has no fields")
        return fields

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename

    def _module_local_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parent / filename
