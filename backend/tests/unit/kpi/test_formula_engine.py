import pytest

from app.modules.kpi.application.formula_dependency_resolver import FormulaDependencyResolver
from app.modules.kpi.application.formula_engine_api import FormulaEngineInternalAPI
from app.modules.kpi.application.ports.catalog_reader import CanonicalModelReader, FormulaCatalogReader
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition, FormulaEvaluationRequest
from app.modules.kpi.domain.formula_engine_errors import FormulaDependencyError, FormulaValidationError
from app.modules.kpi.infrastructure.formula_catalog_yaml import YamlCanonicalModelReader, YamlFormulaCatalogReader


def test_formula_engine_evaluates_official_net_revenue_formula() -> None:
    engine = FormulaEngineInternalAPI(
        formula_catalog=YamlFormulaCatalogReader(),
        canonical_model=YamlCanonicalModelReader(),
    )

    result = engine.evaluate_formula(
        FormulaEvaluationRequest(
            formula_id="revenue.net",
            company_id="cmp_acme",
            period_ref="2026-07",
            metrics={
                "fact_sales.gross_revenue": 1000,
                "fact_sales.tax_amount": 100,
                "fact_sales.return_amount": 50,
                "fact_sales.discount_amount": 20,
            },
        )
    )

    assert result.value == 830.0
    assert result.unit == "BRL"
    assert result.audit.formula_id == "revenue.net"
    assert result.audit.inputs_used["fact_sales.gross_revenue"] == 1000


class _CatalogWithUndeclaredIdentifier(FormulaCatalogReader):
    def load_formulas(self) -> dict[str, FormulaDefinition]:
        return {
            "f.bad": FormulaDefinition(
                formula_id="f.bad",
                kpi_id="X-01",
                name="bad",
                expression="sum(injected_identifier)",
                input_metrics=("fact_sales.gross_revenue",),
                output_type="decimal",
                output_unit="BRL",
                precision=2,
                owner="test",
                version=1,
                effective_from="2026-07-12",
            )
        }


class _Canonical(CanonicalModelReader):
    def load_canonical_fields(self) -> set[str]:
        return {"fact_sales.gross_revenue"}


def test_formula_engine_rejects_undeclared_identifier() -> None:
    engine = FormulaEngineInternalAPI(formula_catalog=_CatalogWithUndeclaredIdentifier(), canonical_model=_Canonical())

    with pytest.raises(FormulaValidationError):
        engine.evaluate_formula(
            FormulaEvaluationRequest(
                formula_id="f.bad",
                company_id="cmp",
                period_ref="2026-07",
                metrics={"fact_sales.gross_revenue": 10},
            )
        )


def test_dependency_resolver_detects_cycle() -> None:
    resolver = FormulaDependencyResolver()
    formulas = {
        "f.a": FormulaDefinition(
            formula_id="f.a",
            kpi_id="X",
            name="A",
            expression="add(f.b,1)",
            input_metrics=("f.b",),
            output_type="decimal",
            output_unit="n",
            precision=2,
            owner="test",
            version=1,
            effective_from="2026-07-12",
        ),
        "f.b": FormulaDefinition(
            formula_id="f.b",
            kpi_id="Y",
            name="B",
            expression="add(f.a,1)",
            input_metrics=("f.a",),
            output_type="decimal",
            output_unit="n",
            precision=2,
            owner="test",
            version=1,
            effective_from="2026-07-12",
        ),
    }

    with pytest.raises(FormulaDependencyError):
        resolver.resolve_order(formulas)
