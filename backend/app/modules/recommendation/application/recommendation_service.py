from __future__ import annotations

from dataclasses import dataclass

from app.modules.recommendation.application.dsl_evaluator import eval_expression
from app.modules.recommendation.application.recommendation_builder import RecommendationBuilder
from app.modules.recommendation.application.recommendation_prioritizer import RecommendationPrioritizer
from app.modules.recommendation.application.recommendation_publisher import RecommendationPublisher
from app.modules.recommendation.domain.entities import RecommendationAggregate, RecommendationDefinition
from app.modules.recommendation.domain.errors import RecommendationEvaluationError


@dataclass(slots=True)
class RecommendationService:
    repository: object
    builder: RecommendationBuilder
    prioritizer: RecommendationPrioritizer
    publisher: RecommendationPublisher

    def generate(
        self,
        *,
        company_id: str,
        period_ref: str,
        orchestrator_run_id: str,
        definitions: tuple[RecommendationDefinition, ...],
        source_event_id: str | None,
    ) -> tuple[tuple[RecommendationAggregate, ...], int, int, tuple[str, ...]]:
        kpi_context = self.repository.load_kpi_context(company_id=company_id, period_ref=period_ref)
        rule_results = self.repository.load_rule_results(company_id=company_id, period_ref=period_ref)

        generated: list[RecommendationAggregate] = []
        deduplicated = 0

        by_rule: dict[str, list[RecommendationDefinition]] = {}
        for definition in definitions:
            by_rule.setdefault(definition.trigger_rule_id, []).append(definition)

        for rule in rule_results:
            defs = by_rule.get(rule.rule_id, [])
            for definition in defs:
                if self.repository.has_recommendation_result(
                    company_id=company_id,
                    period_ref=period_ref,
                    recommendation_id=definition.recommendation_id,
                ):
                    deduplicated += 1
                    self.repository.add_audit(
                        company_id=company_id,
                        period_ref=period_ref,
                        recommendation_id=definition.recommendation_id,
                        trigger_rule_id=definition.trigger_rule_id,
                        status="idempotent",
                        details={"reason": "dedup hit"},
                        orchestrator_run_id=orchestrator_run_id,
                    )
                    continue

                context = {
                    "metric_value": rule.metric_value,
                    "severity": rule.severity,
                    "priority": rule.priority,
                    **kpi_context,
                }
                applicable = self._is_applicable(definition, context)
                if not applicable:
                    self.repository.add_audit(
                        company_id=company_id,
                        period_ref=period_ref,
                        recommendation_id=definition.recommendation_id,
                        trigger_rule_id=definition.trigger_rule_id,
                        status="skipped",
                        details={"reason": "applicability false"},
                        orchestrator_run_id=orchestrator_run_id,
                    )
                    continue

                expected_impact_value = float(eval_expression(definition.expected_impact_formula, context))
                impact_score = self.prioritizer.impact_score(expected_impact_value)
                urgency_score = self.prioritizer.urgency_score(
                    severity=rule.severity,
                    sla_target=definition.sla_target,
                )
                effort_score = self.prioritizer.effort_score(definition.effort_level)
                rank_score = self.prioritizer.rank_score(
                    impact_score=impact_score,
                    urgency_score=urgency_score,
                    effort_score=effort_score,
                    confidence_score=definition.confidence_score,
                )

                built = self.builder.build(
                    definition=definition,
                    company_id=company_id,
                    period_ref=period_ref,
                    orchestrator_run_id=orchestrator_run_id,
                    trigger_rule_id=definition.trigger_rule_id,
                    expected_impact_value=expected_impact_value,
                    impact_score=impact_score,
                    urgency_score=urgency_score,
                    effort_score=effort_score,
                    rank_score=rank_score,
                )
                self.repository.save_recommendation_result(built)
                self.repository.add_audit(
                    company_id=company_id,
                    period_ref=period_ref,
                    recommendation_id=definition.recommendation_id,
                    trigger_rule_id=definition.trigger_rule_id,
                    status="generated",
                    details={
                        "rank_score": rank_score,
                        "impact_score": impact_score,
                        "urgency_score": urgency_score,
                        "effort_score": effort_score,
                    },
                    orchestrator_run_id=orchestrator_run_id,
                )
                generated.append(built)

        grouped = self._group_recommendations(generated)
        ordered = tuple(sorted(grouped, key=lambda item: item.rank_score, reverse=True))

        event_ids: list[str] = []
        for recommendation in ordered:
            event_ids.append(self.publisher.publish(recommendation, source_event_id))

        return ordered, deduplicated, len(grouped), tuple(event_ids)

    def _is_applicable(self, definition: RecommendationDefinition, context: dict[str, object]) -> bool:
        for condition in definition.applicability_conditions:
            value = eval_expression(condition, context)
            if not bool(value):
                return False
        return True

    def _group_recommendations(self, generated: list[RecommendationAggregate]) -> list[RecommendationAggregate]:
        grouped: dict[str, RecommendationAggregate] = {}
        for item in generated:
            current = grouped.get(item.group_key)
            if current is None or item.rank_score > current.rank_score:
                grouped[item.group_key] = item
        return list(grouped.values())
