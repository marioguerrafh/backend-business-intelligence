from app.modules.executive_presentation.application.catalog import PresentationCatalog


def test_presentation_catalog_has_required_sections() -> None:
    catalog = PresentationCatalog().load()

    assert "kpis" in catalog
    assert "alerts" in catalog
    assert "insights" in catalog
    assert "severity" in catalog
    assert "score" in catalog
    assert "highlights" in catalog
    assert "sections" in catalog
    assert isinstance(catalog["sections"], list)
    assert catalog["sections"][0]["type"] == "hero"
