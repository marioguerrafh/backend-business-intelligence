from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.modules.executive_score.application.contracts import (
    CalculateExecutiveScoreCommand,
    CalculateExecutiveScoreResult,
)
from app.modules.insight.application.contracts import GenerateInsightsCommand, GenerateInsightsResult
from app.modules.imports.application.contracts import ImportTemplate
from app.modules.kpi.application.orchestrator_contracts import IngestCompletedEvent, OrchestratorResult
from app.modules.recommendation.application.contracts import (
    GenerateRecommendationsCommand,
    GenerateRecommendationsResult,
)
from app.modules.rule.application.contracts import ExecuteRulesCommand, ExecuteRulesResult
from app.modules.summary.application.contracts import GetSummaryQuery
from app.modules.summary.application.summary_service import SummaryResult


class KPIOrchestrator(Protocol):
    def execute(self, event: IngestCompletedEvent) -> OrchestratorResult: ...


class RuleEngine(Protocol):
    def execute(self, command: ExecuteRulesCommand) -> ExecuteRulesResult: ...


class RecommendationEngine(Protocol):
    def execute(self, command: GenerateRecommendationsCommand) -> GenerateRecommendationsResult: ...


class InsightEngine(Protocol):
    def execute(self, command: GenerateInsightsCommand) -> GenerateInsightsResult: ...


class ExecutiveScoreEngine(Protocol):
    def execute(self, command: CalculateExecutiveScoreCommand) -> CalculateExecutiveScoreResult: ...


class SummaryServiceLike(Protocol):
    def get_summary(self, query: GetSummaryQuery) -> SummaryResult: ...


@dataclass(slots=True)
class PipelineExecutionContext:
    company_id: str
    import_job_id: str
    template: ImportTemplate
    source_system: str
    ingest_event_id: str | None
    correlation_id: str | None
    period_ref: str | None = None
    orchestrator_run_id: str | None = None


@dataclass(slots=True)
class PipelineExecutor:
    kpi_orchestrator: KPIOrchestrator
    rule_engine: RuleEngine
    recommendation_engine: RecommendationEngine
    insight_engine: InsightEngine
    executive_score_engine: ExecutiveScoreEngine
    summary_service: SummaryServiceLike

    def run_kpi_orchestrator(self, *, context: PipelineExecutionContext, fallback_run_id: str) -> dict[str, object]:
        result = self.kpi_orchestrator.execute(
            IngestCompletedEvent(
                company_id=context.company_id,
                import_job_id=context.import_job_id,
                template=context.template,
                source_system=context.source_system,
                event_id=context.ingest_event_id,
                orchestrator_run_id=fallback_run_id,
                period_ref=context.period_ref,
                correlation_id=context.correlation_id,
            )
        )
        if not result.periods:
            raise ValueError("kpi orchestrator returned no periods")

        period_items = [
            {
                "period_ref": item.period_ref,
                "orchestrator_run_id": item.orchestrator_run_id,
                "status": item.status,
                "recalculated_count": item.recalculated_count,
                "failed_count": item.failed_count,
                "idempotent_hit": item.idempotent_hit,
            }
            for item in result.periods
        ]

        primary = result.periods[0]
        context.period_ref = primary.period_ref
        context.orchestrator_run_id = primary.orchestrator_run_id

        return {
            "source_event_topic": result.source_event_topic,
            "source_event_id": result.source_event_id,
            "period_ref": primary.period_ref,
            "orchestrator_run_id": primary.orchestrator_run_id,
            "status": primary.status,
            "recalculated_count": primary.recalculated_count,
            "failed_count": primary.failed_count,
            "idempotent_hit": primary.idempotent_hit,
            "total_periods": len(period_items),
            "periods": period_items,
        }

    def run_rule_engine(
        self,
        *,
        context: PipelineExecutionContext,
        period_ref: str,
        orchestrator_run_id: str,
    ) -> dict[str, object]:
        self._assert_period_context(period_ref=period_ref, orchestrator_run_id=orchestrator_run_id)
        result = self.rule_engine.execute(
            ExecuteRulesCommand(
                company_id=context.company_id,
                period_ref=period_ref,
                orchestrator_run_id=orchestrator_run_id,
                correlation_id=context.correlation_id,
                source_event_id=context.ingest_event_id,
            )
        )
        return {
            "evaluated_rules": result.evaluated_rules,
            "fired_rules": result.fired_rules,
            "idempotent_hits": result.idempotent_hits,
        }

    def run_recommendation_engine(
        self,
        *,
        context: PipelineExecutionContext,
        period_ref: str,
        orchestrator_run_id: str,
    ) -> dict[str, object]:
        self._assert_period_context(period_ref=period_ref, orchestrator_run_id=orchestrator_run_id)
        result = self.recommendation_engine.execute(
            GenerateRecommendationsCommand(
                company_id=context.company_id,
                period_ref=period_ref,
                orchestrator_run_id=orchestrator_run_id,
                source_event_id=context.ingest_event_id,
                correlation_id=context.correlation_id,
            )
        )
        return {
            "generated_count": result.generated_count,
            "deduplicated_count": result.deduplicated_count,
            "grouped_count": result.grouped_count,
        }

    def run_insight_engine(
        self,
        *,
        context: PipelineExecutionContext,
        period_ref: str,
        orchestrator_run_id: str,
    ) -> dict[str, object]:
        self._assert_period_context(period_ref=period_ref, orchestrator_run_id=orchestrator_run_id)
        result = self.insight_engine.execute(
            GenerateInsightsCommand(
                company_id=context.company_id,
                period_ref=period_ref,
                orchestrator_run_id=orchestrator_run_id,
                source_event_id=context.ingest_event_id,
                correlation_id=context.correlation_id,
            )
        )
        return {
            "generated_count": result.generated_count,
        }

    def run_executive_score_engine(
        self,
        *,
        context: PipelineExecutionContext,
        period_ref: str,
        orchestrator_run_id: str,
    ) -> dict[str, object]:
        self._assert_period_context(period_ref=period_ref, orchestrator_run_id=orchestrator_run_id)
        result = self.executive_score_engine.execute(
            CalculateExecutiveScoreCommand(
                company_id=context.company_id,
                period_ref=period_ref,
                orchestrator_run_id=orchestrator_run_id,
                source_event_id=context.ingest_event_id,
                correlation_id=context.correlation_id,
            )
        )
        return {
            "executive_score": result.executive_score,
            "financial_score": result.financial_score,
            "commercial_score": result.commercial_score,
            "operational_score": result.operational_score,
            "inventory_score": result.inventory_score,
        }

    def run_summary_engine(
        self,
        *,
        context: PipelineExecutionContext,
        period_ref: str,
        orchestrator_run_id: str,
    ) -> dict[str, object]:
        self._assert_period_context(period_ref=period_ref, orchestrator_run_id=orchestrator_run_id)
        result = self.summary_service.get_summary(
            GetSummaryQuery(
                company_id=context.company_id,
                period_ref=period_ref,
                correlation_id=context.correlation_id,
                force_refresh=True,
            )
        )
        return {
            "summary_updated": True,
            "cache_hit": result.cache_hit,
            "summary_id": result.payload.get("summary_id"),
            "period_ref": result.payload.get("period_ref"),
        }

    @staticmethod
    def _assert_period_context(*, period_ref: str, orchestrator_run_id: str) -> None:
        if not period_ref:
            raise ValueError("pipeline context missing period_ref")
        if not orchestrator_run_id:
            raise ValueError("pipeline context missing orchestrator_run_id")
