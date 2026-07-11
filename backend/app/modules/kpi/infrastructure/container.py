from app.modules.kpi.application.formula_engine_api import FormulaEngineInternalAPI
from app.modules.kpi.application.orchestrator_use_case import KPIOrchestratorUseCase
from app.modules.kpi.infrastructure.formula_catalog_yaml import (
    YamlCanonicalModelReader,
    YamlFormulaCatalogReader,
)
from app.modules.kpi.infrastructure.repositories import KPIOrchestratorRepository


def build_formula_engine_internal_api() -> FormulaEngineInternalAPI:
    return FormulaEngineInternalAPI(
        formula_catalog=YamlFormulaCatalogReader(),
        canonical_model=YamlCanonicalModelReader(),
    )


def build_kpi_orchestrator_use_case(session) -> KPIOrchestratorUseCase:
    formula_catalog = YamlFormulaCatalogReader()
    return KPIOrchestratorUseCase(
        repository=KPIOrchestratorRepository(session=session),
        formula_catalog=formula_catalog,
        formula_engine_api=FormulaEngineInternalAPI(
            formula_catalog=formula_catalog,
            canonical_model=YamlCanonicalModelReader(),
        ),
    )
