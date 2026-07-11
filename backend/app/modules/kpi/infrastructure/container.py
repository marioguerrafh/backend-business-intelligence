from app.modules.kpi.application.formula_engine_api import FormulaEngineInternalAPI
from app.modules.kpi.infrastructure.formula_catalog_yaml import (
    YamlCanonicalModelReader,
    YamlFormulaCatalogReader,
)


def build_formula_engine_internal_api() -> FormulaEngineInternalAPI:
    return FormulaEngineInternalAPI(
        formula_catalog=YamlFormulaCatalogReader(),
        canonical_model=YamlCanonicalModelReader(),
    )
