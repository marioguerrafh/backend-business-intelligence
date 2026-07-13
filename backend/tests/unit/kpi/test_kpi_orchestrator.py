from __future__ import annotations

from dataclasses import dataclass

from app.modules.kpi.application.formula_engine_api import FormulaEngineInternalAPI
from app.modules.kpi.application.orchestrator_contracts import IngestCompletedEvent
from app.modules.kpi.application.orchestrator_use_case import ExistingRun, KPIOrchestratorUseCase
from app.modules.kpi.application.ports.catalog_reader import CanonicalModelReader, FormulaCatalogReader
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition


class _Catalog(FormulaCatalogReader):
    def load_formulas(self) -> dict[str, FormulaDefinition]:
        return {
            "f.net_revenue": FormulaDefinition(
                formula_id="f.net_revenue",
                kpi_id="FIN-01",
                name="receita_liquida",
                expression="sub(sum(gross_revenue), sum(tax_amount))",
                input_metrics=("fact_sales.gross_revenue", "fact_sales.tax_amount"),
                output_type="decimal",
                output_unit="BRL",
                precision=2,
                owner="financeiro",
                version=1,
            ),
            "f.net_revenue_ratio": FormulaDefinition(
                formula_id="f.net_revenue_ratio",
                kpi_id="FIN-99",
                name="ratio_receita",
                expression="div(f.net_revenue, 100)",
                input_metrics=("formula:f.net_revenue",),
                output_type="decimal",
                output_unit="ratio",
                precision=2,
                owner="financeiro",
                version=1,
            ),
            "f.cashflow_operating": FormulaDefinition(
                formula_id="f.cashflow_operating",
                kpi_id="FIN-03",
                name="fluxo_caixa_operacional",
                expression="sum(fact_finance_cashflow.operating_cash_flow_amount)",
                input_metrics=("fact_finance_cashflow.operating_cash_flow_amount",),
                output_type="decimal",
                output_unit="BRL",
                precision=2,
                owner="tesouraria",
                version=1,
            ),
        }


class _Canonical(CanonicalModelReader):
    def load_canonical_fields(self) -> set[str]:
        return {
            "fact_sales.gross_revenue",
            "fact_sales.tax_amount",
            "fact_finance_cashflow.operating_cash_flow_amount",
        }


@dataclass
class _FakeRepo:
    period_metrics: dict[str, dict[str, float]]
    existing: dict[tuple[str, str, str], ExistingRun]

    def __post_init__(self) -> None:
        self.started: list[tuple[str, str, str]] = []
        self.finished: list[tuple[str, str, str]] = []
        self.persisted: list[tuple[str, str, str, str]] = []
        self.audits: list[tuple[str, str, str, str]] = []
        self.events: list[tuple[str, str, str, str]] = []

    def existing_run(self, *, company_id: str, period_ref: str, orchestrator_run_id: str) -> ExistingRun | None:
        return self.existing.get((company_id, period_ref, orchestrator_run_id))

    def start_run(self, *, company_id: str, period_ref: str, orchestrator_run_id: str, correlation_id: str | None) -> None:
        self.started.append((company_id, period_ref, orchestrator_run_id))

    def finish_run(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        status: str,
        error_summary: str | None,
    ) -> None:
        self.finished.append((company_id, period_ref, status))

    def resolve_period_metrics(self, *, company_id: str, import_job_id: str, template: str) -> dict[str, dict[str, float]]:
        return self.period_metrics

    def resolve_import_job_period(self, *, company_id: str, import_job_id: str) -> str:
        return "2026-07"

    def upsert_kpi_result(self, **kwargs) -> None:
        self.persisted.append((kwargs["period_ref"], kwargs["formula_id"], kwargs["kpi_id"], kwargs["orchestrator_run_id"]))

    def add_audit_entry(self, **kwargs) -> None:
        self.audits.append((kwargs["period_ref"], kwargs["formula_id"], kwargs["kpi_id"], kwargs["status"]))

    def publish_kpi_recalculated(self, **kwargs) -> str:
        event_id = f"evt_{len(self.events)+1}"
        self.events.append((kwargs["period_ref"], kwargs["formula_id"], kwargs["kpi_id"], event_id))
        return event_id


def _build_use_case(repo: _FakeRepo) -> KPIOrchestratorUseCase:
    catalog = _Catalog()
    engine = FormulaEngineInternalAPI(formula_catalog=catalog, canonical_model=_Canonical())
    return KPIOrchestratorUseCase(repository=repo, formula_catalog=catalog, formula_engine_api=engine)


def test_orchestrator_resolves_dependencies_and_publishes_for_impacted_formula() -> None:
    repo = _FakeRepo(
        period_metrics={
            "2026-07": {
                "fact_sales.gross_revenue": 1000.0,
                "fact_sales.tax_amount": 100.0,
                "fact_finance_cashflow.operating_cash_flow_amount": 123.0,
            }
        },
        existing={},
    )
    use_case = _build_use_case(repo)

    result = use_case.execute(
        IngestCompletedEvent(
            company_id="cmp_acme",
            import_job_id="imp_001",
            template="sales",
            source_system="csv_manual",
            orchestrator_run_id="run_001",
        )
    )

    assert len(result.periods) == 1
    period = result.periods[0]
    assert period.idempotent_hit is False
    assert period.recalculated_count == 3
    assert period.failed_count == 0
    assert len(repo.persisted) == 3
    assert any(item[1] == "f.net_revenue" for item in repo.persisted)
    assert any(item[1] == "f.net_revenue_ratio" for item in repo.persisted)
    assert any(item[1] == "f.cashflow_operating" for item in repo.persisted)


def test_orchestrator_is_idempotent_for_same_company_period_and_run() -> None:
    existing = ExistingRun(orchestrator_run_id="run_001", status="success")
    repo = _FakeRepo(
        period_metrics={"2026-07": {"fact_sales.gross_revenue": 1000.0, "fact_sales.tax_amount": 100.0}},
        existing={("cmp_acme", "2026-07", "run_001"): existing},
    )
    use_case = _build_use_case(repo)

    result = use_case.execute(
        IngestCompletedEvent(
            company_id="cmp_acme",
            import_job_id="imp_001",
            template="sales",
            source_system="csv_manual",
            orchestrator_run_id="run_001",
        )
    )

    assert len(result.periods) == 1
    period = result.periods[0]
    assert period.idempotent_hit is True
    assert period.status == "success"
    assert period.recalculated_count == 0
    assert repo.persisted == []
    assert repo.events == []


def test_orchestrator_treats_cashflow_template_as_financial_metrics() -> None:
    repo = _FakeRepo(
        period_metrics={"2026-07": {"fact_finance_cashflow.operating_cash_flow_amount": 123.0}},
        existing={},
    )
    use_case = _build_use_case(repo)

    result = use_case.execute(
        IngestCompletedEvent(
            company_id="cmp_acme",
            import_job_id="imp_002",
            template="cashflow",
            source_system="csv_manual",
            orchestrator_run_id="run_002",
        )
    )

    assert len(result.periods) == 1
    period = result.periods[0]
    assert period.recalculated_count == 1
    assert any(item[1] == "f.cashflow_operating" for item in repo.persisted)


def test_orchestrator_sales_template_expands_to_full_fact_domains() -> None:
    repo = _FakeRepo(period_metrics={"2026-07": {}}, existing={})
    use_case = _build_use_case(repo)

    formulas = {
        "f.sales": FormulaDefinition(
            formula_id="f.sales",
            kpi_id="FIN-10",
            name="sales",
            expression="sum(fact_sales.net_revenue)",
            input_metrics=("fact_sales.net_revenue",),
            output_type="decimal",
            output_unit="BRL",
            precision=2,
            owner="financeiro",
            version=1,
        ),
        "f.service": FormulaDefinition(
            formula_id="f.service",
            kpi_id="OPR-20",
            name="service",
            expression="sum(fact_service.orders)",
            input_metrics=("fact_service.orders",),
            output_type="decimal",
            output_unit="count",
            precision=2,
            owner="operacoes",
            version=1,
        ),
        "f.production": FormulaDefinition(
            formula_id="f.production",
            kpi_id="OPR-21",
            name="production",
            expression="sum(fact_production.units)",
            input_metrics=("fact_production.units",),
            output_type="decimal",
            output_unit="count",
            precision=2,
            owner="operacoes",
            version=1,
        ),
    }

    impacted = use_case._impacted_formula_ids(template="sales", formulas=formulas)

    assert impacted == {"f.sales", "f.service", "f.production"}
