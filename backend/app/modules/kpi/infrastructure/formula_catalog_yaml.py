from pathlib import Path

import yaml

from app.modules.kpi.application.ports.catalog_reader import CanonicalModelReader, FormulaCatalogReader
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition
from app.modules.kpi.domain.formula_engine_errors import FormulaValidationError


class YamlFormulaCatalogReader(FormulaCatalogReader):
    def __init__(self, formula_dsl_path: Path | None = None) -> None:
        self.formula_dsl_path = formula_dsl_path or self._default_path("formula-dsl.v1.yaml")

    def load_formulas(self) -> dict[str, FormulaDefinition]:
        try:
            with self.formula_dsl_path.open("r", encoding="utf-8") as fp:
                payload = yaml.safe_load(fp) or {}
        except FileNotFoundError as exc:
            fallback_path = self._module_local_path("formula-dsl.v1.yaml")
            if fallback_path != self.formula_dsl_path and fallback_path.exists():
                with fallback_path.open("r", encoding="utf-8") as fp:
                    payload = yaml.safe_load(fp) or {}
            else:
                raise FormulaValidationError(
                    f"formula catalog file not found: {self.formula_dsl_path}"
                ) from exc

        examples = payload.get("formula_examples", [])
        formulas: dict[str, FormulaDefinition] = {}
        for item in examples:
            definition = FormulaDefinition(
                formula_id=item["formula_id"],
                kpi_id=item["kpi_id"],
                name=item["name"],
                expression=item["expression"],
                input_metrics=tuple(item.get("input_metrics", [])),
                output_type=item["output_type"],
                output_unit=item["output_unit"],
                precision=int(item.get("precision", 2)),
                owner=item.get("owner", "unknown"),
                version=int(item.get("version", 1)),
            )
            formulas[definition.formula_id] = definition

        if not formulas:
            raise FormulaValidationError("formula catalog is empty")
        return formulas

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename

    def _module_local_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parent / filename


class YamlCanonicalModelReader(CanonicalModelReader):
    def __init__(self, canonical_model_path: Path | None = None) -> None:
        self.canonical_model_path = canonical_model_path or self._default_path("canonical-data-model.v1.yaml")

    def load_canonical_fields(self) -> set[str]:
        try:
            with self.canonical_model_path.open("r", encoding="utf-8") as fp:
                payload = yaml.safe_load(fp) or {}
        except FileNotFoundError as exc:
            fallback_path = self._module_local_path("canonical-data-model.v1.yaml")
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
