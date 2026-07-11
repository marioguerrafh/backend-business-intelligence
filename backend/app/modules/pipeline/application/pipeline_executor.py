from __future__ import annotations

from dataclasses import dataclass

from app.modules.executive_score.application.contracts import CalculateExecutiveScoreCommand
from app.modules.insight.application.contracts import GenerateInsightsCommand
from app.modules.kpi.application.orchestrator_contracts import IngestCompletedEvent
from app.modules.recommendation.application.contracts import GenerateRecommendationsCommand
from app.modules.rule.application.contracts import ExecuteRulesCommand
from app.modules.summary.application.contracts import GetSummaryQuery


@dataclass(slots=True)
class PipelineExecutionContext:
    company_id: str
    import_job_id: str
    template: str
    source_system: str
    ingest_event_id: str | None
    correlation_id: str | None
    period_ref: str | None = None
    orchestrator_run_id: str | None = None


@dataclass(slots=True)
class PipelineExecutor:
    kpi_orchestrator: object
    rule_engine: object
    recommendation_engine: object
    insight_engine: object
    executive_score_engine: object
    summary_service: object

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

        period_item = result.periods[0]
        context.period_ref = period_item.period_ref
        context.orchestrator_run_id = period_item.orchestrator_run_id

        return {
            "source_event_topic": result.source_event_topic,
            "source_event_id": result.source_event_id,
            "period_ref": period_item.period_ref,
            "orchestrator_run_id": period_item.orchestrator_run_id,
            "status": period_item.status,
            "recalculated_count": period_item.recalculated_count,
            "failed_count": period_item.failed_count,
            "idempotent_hit": period_item.idempotent_hit,
        }

    def run_rule_engine(self, *, context: PipelineExecutionContext) -> dict[str, object]:
        self._assert_context(context)
        result = self.rule_engine.execute(
            ExecuteRulesCommand(
                company_id=context.company_id,
                period_ref=context.period_ref or "",
                orchestrator_run_id=context.orchestrator_run_id or "",
                correlation_id=context.correlation_id,
                source_event_id=context.ingest_event_id,
            )
        )
        return {
            "evaluated_rules": result.evaluated_rules,
            "fired_rules": result.fired_rules,
            "idempotent_hits": result.idempotent_hits,
        }

    def run_recommendation_engine(self, *, context: PipelineExecutionContext) -> dict[str, object]:
        self._assert_context(context)
        result = self.recommendation_engine.execute(
            GenerateRecommendationsCommand(
                company_id=context.company_id,
                period_ref=context.period_ref or "",
                orchestrator_run_id=context.orchestrator_run_id or "",
                source_event_id=context.ingest_event_id,
                correlation_id=context.correlation_id,
            )
        )
        return {
            "generated_count": result.generated_count,
            "deduplicated_count": result.deduplicated_count,
            "grouped_count": result.grouped_count,
        }

    def run_insight_engine(self, *, context: PipelineExecutionContext) -> dict[str, object]:
        self._assert_context(context)
        result = self.insight_engine.execute(
            GenerateInsightsCommand(
                company_id=context.company_id,
                period_ref=context.period_ref or "",
                orchestrator_run_id=context.orchestrator_run_id or "",
                source_event_id=context.ingest_event_id,
                correlation_id=context.correlation_id,
            )
        )
        return {
            "generated_count": result.generated_count,
        }

    def run_executive_score_engine(self, *, context: PipelineExecutionContext) -> dict[str, object]:
        self._assert_context(context)
        result = self.executive_score_engine.execute(
            CalculateExecutiveScoreCommand(
                company_id=context.company_id,
                period_ref=context.period_ref or "",
                orchestrator_run_id=context.orchestrator_run_id or "",
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

    def run_summary_engine(self, *, context: PipelineExecutionContext) -> dict[str, object]:
        self._assert_context(context)
        result = self.summary_service.get_summary(
            GetSummaryQuery(
                company_id=context.company_id,
                period_ref=context.period_ref,
                correlation_id=context.correlation_id,
            )
        )
        return {
            "summary_updated": True,
            "cache_hit": result.cache_hit,
            "summary_id": result.payload.get("summary_id"),
            "period_ref": result.payload.get("period_ref"),
        }

    @staticmethod
    def _assert_context(context: PipelineExecutionContext) -> None:
        if not context.period_ref:
            raise ValueError("pipeline context missing period_ref")
        if not context.orchestrator_run_id:
            raise ValueError("pipeline context missing orchestrator_run_id")
