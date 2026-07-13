from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

import yaml


@dataclass(slots=True)
class _CatalogCache:
    path: Path
    mtime_ns: int
    payload: dict[str, Any]


_CACHE: _CatalogCache | None = None
_LOCK = Lock()


class PresentationCatalog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._default_path("presentation-catalog.v1.yaml")

    def load(self) -> dict[str, Any]:
        global _CACHE

        path = self._resolve_path()
        stat = path.stat()

        with _LOCK:
            if _CACHE and _CACHE.path == path and _CACHE.mtime_ns == stat.st_mtime_ns:
                return _CACHE.payload

            with path.open("r", encoding="utf-8") as fp:
                payload = yaml.safe_load(fp) or {}

            if not isinstance(payload, dict):
                raise ValueError("presentation catalog must be an object")

            payload = self._merge_kpi_catalog(payload)

            _CACHE = _CatalogCache(path=path, mtime_ns=stat.st_mtime_ns, payload=payload)
            return payload

    def _resolve_path(self) -> Path:
        if self.path.exists():
            return self.path
        fallback = self._module_local_path("presentation_catalog.yaml")
        if fallback.exists():
            return fallback
        raise ValueError(f"presentation catalog file not found: {self.path}")

    def _merge_kpi_catalog(self, payload: dict[str, Any]) -> dict[str, Any]:
        kpi_path = self._default_path("kpi-catalog.v1.yaml")
        if not kpi_path.exists():
            return payload

        with kpi_path.open("r", encoding="utf-8") as fp:
            kpi_payload = yaml.safe_load(fp) or {}

        official_kpis = kpi_payload.get("kpis", {}) if isinstance(kpi_payload, dict) else {}
        if not isinstance(official_kpis, dict):
            return payload

        merged_kpis: dict[str, Any] = {}
        for kpi_id, item in official_kpis.items():
            if not isinstance(item, dict):
                continue
            merged_kpis[kpi_id] = {
                "short_name": item.get("short_name", "Indicador"),
                "display_name": item.get("name", item.get("display_name", kpi_id)),
                "description": item.get("description", ""),
                "icon": item.get("icon", "insights"),
                "category": item.get("category", "Executivo"),
                "currency": item.get("unit", "NUMBER"),
                "health": {
                    "green": "good",
                    "yellow": "attention",
                    "red": "critical",
                },
                "comparison": item.get("presentation", {}).get("subtitle", payload.get("strings", {}).get("comparison_last_month", "")),
                "display_order": item.get("display_order", 99),
            }

        current_kpis = payload.get("kpis", {}) if isinstance(payload.get("kpis", {}), dict) else {}
        merged_kpis.update(current_kpis)
        payload = dict(payload)
        payload["kpis"] = merged_kpis
        payload["official_kpi_catalog_version"] = str(kpi_payload.get("metadata", {}).get("version", "1.0.0"))
        payload["official_formula_dsl_version"] = self._read_semantic_version("formula-dsl.v2.yaml", default="2.0.0")
        payload["official_canonical_model_version"] = self._read_semantic_version(
            "canonical-data-model.v2.yaml",
            default="2.0.0",
        )
        return payload

    def _read_semantic_version(self, filename: str, *, default: str) -> str:
        path = self._default_path(filename)
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as fp:
            loaded = yaml.safe_load(fp) or {}
        if not isinstance(loaded, dict):
            return default
        return str(loaded.get("metadata", {}).get("version", default))

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename

    def _module_local_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parent.parent / "infrastructure" / filename
