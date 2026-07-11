from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.insight.application.contracts import GenerateInsightsCommand, GenerateInsightsResult
from app.modules.insight.application.template_renderer import InsightTemplateRenderer
from app.modules.insight.domain.entities import InsightAggregate


@dataclass(slots=True)
class GenerateInsightsUseCase:
    repository: object
    prompt_catalog: object
    renderer: InsightTemplateRenderer

    def execute(self, command: GenerateInsightsCommand) -> GenerateInsightsResult:
        prompts = self.prompt_catalog.load_prompts()
        kpi_context = self.repository.load_kpi_context(company_id=command.company_id, period_ref=command.period_ref)
        fired_rule_ids = self.repository.load_fired_rule_ids(company_id=command.company_id, period_ref=command.period_ref)
        top_recommendations = self.repository.load_top_recommendation_ids(
            company_id=command.company_id,
            period_ref=command.period_ref,
            limit=3,
        )

        event_ids: list[str] = []
        generated_count = 0

        # Generate at most one insight per supported intent per period.
        for prompt in prompts:
            insight_type = prompt.intent
            if self.repository.has_insight(
                company_id=command.company_id,
                period_ref=command.period_ref,
                insight_type=insight_type,
            ):
                self.repository.add_audit(
                    company_id=command.company_id,
                    period_ref=command.period_ref,
                    insight_type=insight_type,
                    status="idempotent",
                    details={"reason": "dedup hit"},
                    orchestrator_run_id=command.orchestrator_run_id,
                )
                continue

            statement, evidence = self.renderer.render(
                template=prompt,
                kpi_context=kpi_context,
                fired_rule_ids=fired_rule_ids,
                selected_recommendation_ids=top_recommendations,
            )

            aggregate = InsightAggregate(
                insight_result_id=f"ins_{uuid4().hex[:16]}",
                company_id=command.company_id,
                period_ref=command.period_ref,
                insight_type=insight_type,
                statement=statement,
                evidence=evidence,
                prompt_id=prompt.prompt_id,
                orchestrator_run_id=command.orchestrator_run_id,
                generated_at=datetime.now(timezone.utc),
            )
            self.repository.save_insight(aggregate)
            self.repository.add_audit(
                company_id=command.company_id,
                period_ref=command.period_ref,
                insight_type=insight_type,
                status="generated",
                details={
                    "prompt_id": prompt.prompt_id,
                    "audience": prompt.audience,
                    "language": prompt.language,
                },
                orchestrator_run_id=command.orchestrator_run_id,
            )
            generated_count += 1

            event_ids.append(
                self.repository.publish_insight_generated(
                    payload={
                        "company_id": command.company_id,
                        "period_ref": command.period_ref,
                        "insight_type": insight_type,
                        "prompt_id": prompt.prompt_id,
                        "orchestrator_run_id": command.orchestrator_run_id,
                        "source_event_id": command.source_event_id,
                    }
                )
            )

        return GenerateInsightsResult(
            company_id=command.company_id,
            period_ref=command.period_ref,
            orchestrator_run_id=command.orchestrator_run_id,
            generated_count=generated_count,
            published_event_ids=tuple(event_ids),
        )
