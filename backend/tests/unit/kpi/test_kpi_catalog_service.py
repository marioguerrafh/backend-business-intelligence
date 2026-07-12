from __future__ import annotations

from pathlib import Path

import yaml

from app.modules.kpi.application.kpi_catalog_service import KpiCatalogService
from app.modules.kpi.infrastructure.kpi_catalog_yaml import YamlKpiCatalogReader


def test_yaml_kpi_catalog_reader_loads_official_catalog() -> None:
    catalog = YamlKpiCatalogReader().load_kpis()

    assert "FIN-01" in catalog
    assert catalog["FIN-01"]["name"] == "Receita Liquida"
    assert catalog["EXE-04"]["category"] == "Executivo"


def test_kpi_catalog_service_searches_by_category_id_formula_and_tag() -> None:
    service = KpiCatalogService(YamlKpiCatalogReader())

    assert service.get_by_id("FIN-01")["short_name"] == "Receita"
    finance = service.get_by_category("Financeiro")
    assert any(item["id"] == "FIN-02" for item in finance)
    assert service.get_by_formula("revenue.net")["id"] == "FIN-01"
    assert any(item["id"] == "FIN-01" for item in service.get_by_tag("receita"))
    assert len(service.list_all()) >= 20


def test_kpi_catalog_service_validates_official_catalog_without_errors() -> None:
    service = KpiCatalogService(YamlKpiCatalogReader())

    assert service.validate() == []


def test_kpi_catalog_service_detects_duplicate_ids_and_cycles(tmp_path: Path) -> None:
    catalog_path = tmp_path / "kpi-catalog.v1.yaml"
    catalog_path.write_text(
        yaml.safe_dump(
            {
                "kpis": {
                    "A": {
                        "id": "A",
                        "code": "a",
                        "name": "A",
                        "short_name": "A",
                        "description": "A",
                        "category": "Financeiro",
                        "subcategory": "X",
                        "unit": "NUMBER",
                        "display_format": "number",
                        "precision": 2,
                        "icon": "insights",
                        "color": "info",
                        "display_order": 1,
                        "formula_id": "a.formula",
                        "formula": "A",
                        "depends_on": ["B"],
                        "source_tables": ["fact_sales"],
                        "business_area": "Financeiro",
                        "health_ranges": {"excellent": {"min": 95}, "good": {"min": 80}, "attention": {"min": 60}, "critical": {"min": 0}},
                        "trend_strategy": "compare_previous_month",
                        "presentation": {"title": "A", "subtitle": "A", "empty_message": "A", "tooltip": "A", "card_style": "premium"},
                        "tags": ["a"],
                        "owner": "financeiro",
                    },
                    "B": {
                        "id": "B",
                        "code": "b",
                        "name": "B",
                        "short_name": "B",
                        "description": "B",
                        "category": "Financeiro",
                        "subcategory": "X",
                        "unit": "NUMBER",
                        "display_format": "number",
                        "precision": 2,
                        "icon": "insights",
                        "color": "info",
                        "display_order": 2,
                        "formula_id": "b.formula",
                        "formula": "B",
                        "depends_on": ["A"],
                        "source_tables": ["fact_sales"],
                        "business_area": "Financeiro",
                        "health_ranges": {"excellent": {"min": 95}, "good": {"min": 80}, "attention": {"min": 60}, "critical": {"min": 0}},
                        "trend_strategy": "compare_previous_month",
                        "presentation": {"title": "B", "subtitle": "B", "empty_message": "B", "tooltip": "B", "card_style": "premium"},
                        "tags": ["b"],
                        "owner": "financeiro",
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    service = KpiCatalogService(YamlKpiCatalogReader(path=catalog_path))
    errors = service.validate()

    assert any("dependency cycle detected" in error for error in errors)
