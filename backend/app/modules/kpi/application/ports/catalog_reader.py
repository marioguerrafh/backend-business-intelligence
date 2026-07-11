from typing import Protocol

from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition


class FormulaCatalogReader(Protocol):
    def load_formulas(self) -> dict[str, FormulaDefinition]:
        raise NotImplementedError


class CanonicalModelReader(Protocol):
    def load_canonical_fields(self) -> set[str]:
        raise NotImplementedError
