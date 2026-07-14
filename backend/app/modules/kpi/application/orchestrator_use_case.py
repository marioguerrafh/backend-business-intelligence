from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.modules.kpi.application.formula_dependency_resolver import FormulaDependencyResolver
from app.modules.kpi.application.formula_engine_api import FormulaEngineInternalAPI
from app.modules.kpi.application.orchestrator_contracts import IngestCompletedEvent, OrchestratorResult, PeriodRunResult
from app.modules.kpi.application.ports.catalog_reader import FormulaCatalogReader
from app.modules.kpi.domain.formula_engine_entities import FormulaDefinition
from app.modules.kpi.domain.formula_engine_errors import FormulaEngineError


@dataclass(slots=True, frozen=True)
class ExistingRun:
    orchestrator_run_id: str
    status: str


class KPIOrchestratorRepositoryPort(Protocol):
    def existing_run(self, *, company_id: str, period_ref: str, orchestrator_run_id: str) -> ExistingRun | None:
        ...

    def start_run(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        correlation_id: str | None,
    ) -> None:
        ...

    def finish_run(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        status: str,
        error_summary: str | None,
    ) -> None:
        ...

    def resolve_period_metrics(self, *, company_id: str, import_job_id: str, template: str) -> dict[str, dict[str, float]]:
        ...

    def resolve_import_job_period(self, *, company_id: str, import_job_id: str) -> str:
        ...

    def upsert_kpi_result(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        formula_id: str,
        kpi_id: str,
        kpi_name: str,
        value: float,
        unit: str,
        confidence_score: float,
        calculated_at: datetime,
    ) -> None:
        ...

    def add_audit_entry(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        formula_id: str,
        kpi_id: str,
        status: str,
        execution_steps: list[str],
        inputs_used: dict[str, object],
        result_value: float | None,
        error_message: str | None,
    ) -> None:
        ...

    def publish_kpi_recalculated(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        kpi_id: str,
        formula_id: str,
        value: float,
        unit: str,
        confidence_score: float,
    ) -> str:
        ...


@dataclass(slots=True)
class KPIOrchestratorUseCase:
    repository: KPIOrchestratorRepositoryPort
    formula_catalog: FormulaCatalogReader
    formula_engine_api: FormulaEngineInternalAPI
    _resolver: FormulaDependencyResolver = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._resolver = FormulaDependencyResolver()

    def execute(self, event: IngestCompletedEvent) -> OrchestratorResult:
        formulas = self.formula_catalog.load_formulas()
        impacted_formula_ids = self._impacted_formula_ids(template=event.template, formulas=formulas)

        period_metrics = self.repository.resolve_period_metrics(
            company_id=event.company_id,
            import_job_id=event.import_job_id,
            template=event.template,
        )
        if event.period_ref and event.period_ref not in period_metrics:
            period_metrics[event.period_ref] = {}
        if not period_metrics:
            fallback = self.repository.resolve_import_job_period(company_id=event.company_id, import_job_id=event.import_job_id)
            period_metrics[fallback] = {}

        period_results: list[PeriodRunResult] = []
        for period_ref in sorted(period_metrics.keys()):
            run_id = self._build_run_id(
                provided=event.orchestrator_run_id,
                company_id=event.company_id,
                period_ref=period_ref,
                import_job_id=event.import_job_id,
            )

            existing = self.repository.existing_run(
                company_id=event.company_id,
                period_ref=period_ref,
                orchestrator_run_id=run_id,
            )
            if existing is not None:
                period_results.append(
                    PeriodRunResult(
                        period_ref=period_ref,
                        orchestrator_run_id=run_id,
                        status=existing.status,
                        recalculated_count=0,
                        failed_count=0,
                        idempotent_hit=True,
                        published_event_ids=(),
                    )
                )
                continue

            self.repository.start_run(
                company_id=event.company_id,
                period_ref=period_ref,
                orchestrator_run_id=run_id,
                correlation_id=event.correlation_id,
            )

            metrics = dict(period_metrics[period_ref])
            execution_order = self._execution_order(formulas=formulas, impacted_formula_ids=impacted_formula_ids)

            recalculated = 0
            failed = 0
            published_event_ids: list[str] = []
            errors: list[str] = []

            for formula_id in execution_order:
                definition = formulas[formula_id]
                try:
                    result = self.formula_engine_api.evaluate_formula(
                        request=self._build_formula_request(
                            formula_id=formula_id,
                            company_id=event.company_id,
                            period_ref=period_ref,
                            metrics=metrics,
                        )
                    )
                    confidence = 1.0
                    self.repository.upsert_kpi_result(
                        company_id=event.company_id,
                        period_ref=period_ref,
                        orchestrator_run_id=run_id,
                        formula_id=result.formula_id,
                        kpi_id=result.kpi_id,
                        kpi_name=definition.name,
                        value=result.value,
                        unit=result.unit,
                        confidence_score=confidence,
                        calculated_at=result.audit.executed_at,
                    )
                    self.repository.add_audit_entry(
                        company_id=event.company_id,
                        period_ref=period_ref,
                        orchestrator_run_id=run_id,
                        formula_id=result.formula_id,
                        kpi_id=result.kpi_id,
                        status="success",
                        execution_steps=list(result.audit.execution_steps),
                        inputs_used=dict(result.audit.inputs_used),
                        result_value=result.value,
                        error_message=None,
                    )
                    event_id = self.repository.publish_kpi_recalculated(
                        company_id=event.company_id,
                        period_ref=period_ref,
                        orchestrator_run_id=run_id,
                        kpi_id=result.kpi_id,
                        formula_id=result.formula_id,
                        value=result.value,
                        unit=result.unit,
                        confidence_score=confidence,
                    )
                    published_event_ids.append(event_id)

                    metrics[f"formula:{result.formula_id}"] = result.value
                    metrics[f"formula.{result.formula_id}"] = result.value
                    metrics[result.formula_id] = result.value
                    recalculated += 1
                except FormulaEngineError as exc:
                    failed += 1
                    errors.append(str(exc))
                    self.repository.add_audit_entry(
                        company_id=event.company_id,
                        period_ref=period_ref,
                        orchestrator_run_id=run_id,
                        formula_id=formula_id,
                        kpi_id=definition.kpi_id,
                        status="failed",
                        execution_steps=[],
                        inputs_used={},
                        result_value=None,
                        error_message=str(exc),
                    )

            status = self._status(total=len(execution_order), success=recalculated)
            self.repository.finish_run(
                company_id=event.company_id,
                period_ref=period_ref,
                  orchestrator_run_id=run_id,
                status=status,
                error_summary="; ".join(errors) if errors else None,
            )

            period_results.append(
                PeriodRunResult(
                    period_ref=period_ref,
                    orchestrator_run_id=run_id,
                    status=status,
                    recalculated_count=recalculated,
                    failed_count=failed,
                    idempotent_hit=False,
                    published_event_ids=tuple(published_event_ids),
                )
            )

        return OrchestratorResult(
            source_event_topic="ingest.completed.v1",
            source_event_id=event.event_id,
            company_id=event.company_id,
            import_job_id=event.import_job_id,
            periods=tuple(period_results),
        )

    @staticmethod
    def _build_formula_request(*, formula_id: str, company_id: str, period_ref: str, metrics: dict[str, float]):
        from app.modules.kpi.domain.formula_engine_entities import FormulaEvaluationRequest

        return FormulaEvaluationRequest(
            formula_id=formula_id,
            company_id=company_id,
            period_ref=period_ref,
            metrics=metrics,
        )

    @staticmethod
    def _status(*, total: int, success: int) -> str:
        if total == 0:
            return "success"
        if success == 0:
            return "failed"
        if success == total:
            return "success"
        return "partial"

    def _execution_order(self, *, formulas: dict[str, FormulaDefinition], impacted_formula_ids: set[str]) -> list[str]:
        if not impacted_formula_ids:
            return []

        closure: set[str] = set(impacted_formula_ids)
        stack = list(impacted_formula_ids)
        while stack:
            current = stack.pop()
            definition = formulas[current]
            for dependency in self._resolver.dependencies_of(definition):
                if dependency not in closure:
                    closure.add(dependency)
                    stack.append(dependency)

        subgraph = {formula_id: formulas[formula_id] for formula_id in closure}
        return self._resolver.resolve_order(subgraph)

    def _impacted_formula_ids(self, *, template: str, formulas: dict[str, FormulaDefinition]) -> set[str]:
        prefixes_by_template = {
            "sales": ("fact_sales.",),
            "cashflow": ("fact_finance_cashflow.",),
            "financial": ("fact_finance_cashflow.",),
            "balance_sheet": ("fact_balance_sheet.",),
            "income_statement": ("fact_income_statement.",),
            "accounts_receivable": ("fact_accounts_receivable.",),
            "accounts_payable": ("fact_accounts_payable.",),
            "inventory": ("fact_inventory.", "fact_inventory_snapshot."),
            "hr": ("fact_hr.", "fact_hr_workforce."),
            "procurement": ("fact_procurement.",),
            "service": ("fact_service.",),
            "production": ("fact_production.",),
            "customers": ("dim_customer.",),
            "products": ("dim_product.",),
        }
        prefixes = prefixes_by_template.get(template, ())

        # Any factual import should refresh the full KPI fact graph. This avoids
        # partial KPI snapshots (e.g. only 3 KPIs) when historical periods were
        # imported in separate template batches.
        factual_templates = {
            "sales",
            "cashflow",
            "financial",
            "balance_sheet",
            "income_statement",
            "accounts_receivable",
            "accounts_payable",
            "inventory",
            "hr",
        }
        if template in factual_templates:
            prefixes = (
                "fact_sales.",
                "fact_finance_cashflow.",
                "fact_balance_sheet.",
                "fact_income_statement.",
                "fact_accounts_receivable.",
                "fact_accounts_payable.",
                "fact_inventory.",
                "fact_inventory_snapshot.",
                "fact_hr.",
                "fact_hr_workforce.",
                "fact_procurement.",
                "fact_service.",
                "fact_production.",
            )

        direct: set[str] = set()
        for formula_id, definition in formulas.items():
            if any(metric.startswith(prefix) for metric in definition.input_metrics for prefix in prefixes):
                direct.add(formula_id)

        if not direct:
            return set()

        reverse: dict[str, set[str]] = {formula_id: set() for formula_id in formulas}
        for formula_id, definition in formulas.items():
            for dep in self._resolver.dependencies_of(definition):
                reverse.setdefault(dep, set()).add(formula_id)

        impacted: set[str] = set(direct)
        queue = list(direct)
        while queue:
            current = queue.pop()
            for dependent in reverse.get(current, set()):
                if dependent in impacted:
                    continue
                impacted.add(dependent)
                queue.append(dependent)

        return impacted

    @staticmethod
    def _build_run_id(
        *,
        provided: str | None,
        company_id: str,
        period_ref: str,
        import_job_id: str,
    ) -> str:
        if provided:
            return provided
        compact_period = period_ref.replace("-", "")
        base = f"kpi_{company_id}_{compact_period}_{import_job_id}"
        if len(base) <= 64:
            return base
        return f"kpi_{uuid4().hex[:24]}_{compact_period}"
