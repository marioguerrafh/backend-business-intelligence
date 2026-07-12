from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.modules.kpi.application.ports.kpi_catalog_reader import KpiCatalogReader
from app.modules.kpi.domain.formula_engine_errors import FormulaValidationError


class YamlKpiCatalogReader(KpiCatalogReader):
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._default_path("kpi-catalog.v1.yaml")

    def load_kpis(self) -> dict[str, dict[str, Any]]:
        payload = self._read_yaml(self.path)
        raw_kpis = payload.get("kpis", {})
        if not isinstance(raw_kpis, dict) or not raw_kpis:
            raise FormulaValidationError("kpi catalog is empty")

        kpis: dict[str, dict[str, Any]] = {}
        for kpi_id, item in raw_kpis.items():
            if not isinstance(item, dict):
                raise FormulaValidationError(f"kpi catalog item must be an object: {kpi_id}")
            entry = dict(item)
            entry.setdefault("id", kpi_id)
            kpis[kpi_id] = entry
        return kpis

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as fp:
                payload = yaml.safe_load(fp) or {}
        except FileNotFoundError as exc:
            raise FormulaValidationError(f"kpi catalog file not found: {path}") from exc
        if not isinstance(payload, dict):
            raise FormulaValidationError("kpi catalog must be an object")
        return payload

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename
