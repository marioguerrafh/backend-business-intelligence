from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.kpi.application.ports.kpi_catalog_reader import KpiCatalogReader


@dataclass(slots=True, frozen=True)
class KpiCatalogEntry:
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data.get("id") or "")

    @property
    def formula_id(self) -> str:
        return str(self.data.get("formula_id") or "")

    @property
    def category(self) -> str:
        return str(self.data.get("category") or "")


class KpiCatalogService:
    def __init__(self, reader: KpiCatalogReader) -> None:
        self.reader = reader

    def list_all(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.reader.load_kpis().values()]

    def get_by_id(self, kpi_id: str) -> dict[str, Any] | None:
        return self.reader.load_kpis().get(kpi_id)

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        normalized = category.strip().lower()
        return [dict(item) for item in self.reader.load_kpis().values() if str(item.get("category") or "").strip().lower() == normalized]

    def get_by_formula(self, formula_id: str) -> dict[str, Any] | None:
        normalized = formula_id.strip().lower()
        for item in self.reader.load_kpis().values():
            candidates = [str(item.get("formula_id") or "").strip().lower()]
            formula_spec = item.get("formula_spec") if isinstance(item, dict) else None
            if isinstance(formula_spec, dict):
                candidates.append(str(formula_spec.get("formula_id") or "").strip().lower())
            if normalized in candidates:
                return dict(item)
        return None

    def get_by_tag(self, tag: str) -> list[dict[str, Any]]:
        normalized = tag.strip().lower()
        results: list[dict[str, Any]] = []
        for item in self.reader.load_kpis().values():
            tags = [str(value).strip().lower() for value in item.get("tags", [])]
            if normalized in tags:
                results.append(dict(item))
        return results

    def validate(self) -> list[str]:
        kpis = self.reader.load_kpis()
        errors: list[str] = []
        seen_ids: set[str] = set()
        known_categories = {
            "Financeiro",
            "Econômico",
            "Economico",
            "Comercial",
            "Operacional",
            "Produtividade",
            "Estoque",
            "Clientes",
            "RH",
            "Fiscal",
            "Executivo",
        }

        graph: dict[str, list[str]] = {}
        for kpi_id, item in kpis.items():
            if kpi_id in seen_ids:
                errors.append(f"duplicate KPI id: {kpi_id}")
            seen_ids.add(kpi_id)

            missing = [field for field in ("id", "code", "name", "short_name", "description", "category", "subcategory", "unit", "display_format", "precision", "icon", "color", "display_order", "formula_id", "formula", "depends_on", "source_tables", "business_area", "health_ranges", "trend_strategy", "presentation", "tags", "owner") if field not in item]
            if missing:
                errors.append(f"{kpi_id} missing required fields: {', '.join(missing)}")

            if str(item.get("category") or "") not in known_categories:
                errors.append(f"{kpi_id} has invalid category: {item.get('category')}")

            formula_id = str(item.get("formula_id") or "").strip()
            formula = str(item.get("formula") or "").strip()
            if not formula_id:
                errors.append(f"{kpi_id} missing formula_id")
            if not formula:
                errors.append(f"{kpi_id} missing formula")

            deps = [str(dep) for dep in item.get("depends_on", [])]
            graph[kpi_id] = deps
            for dep in deps:
                if dep not in kpis:
                    errors.append(f"{kpi_id} depends on unknown KPI: {dep}")

        if self._has_cycle(graph):
            errors.append("dependency cycle detected")

        return errors

    def _has_cycle(self, graph: dict[str, list[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visited:
                return False
            if node in visiting:
                return True
            visiting.add(node)
            for child in graph.get(node, []):
                if child in graph and visit(child):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in graph)
