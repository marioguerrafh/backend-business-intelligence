from __future__ import annotations

from dataclasses import dataclass

from app.modules.recommendation.application.contracts import (
    GenerateRecommendationsCommand,
    GenerateRecommendationsResult,
)


@dataclass(slots=True)
class GenerateRecommendationsUseCase:
    catalog_reader: object
    service: object

    def execute(self, command: GenerateRecommendationsCommand) -> GenerateRecommendationsResult:
        definitions = self.catalog_reader.load_recommendations()
        generated, deduplicated, grouped_count, event_ids = self.service.generate(
            company_id=command.company_id,
            period_ref=command.period_ref,
            orchestrator_run_id=command.orchestrator_run_id,
            definitions=definitions,
            source_event_id=command.source_event_id,
        )

        return GenerateRecommendationsResult(
            company_id=command.company_id,
            period_ref=command.period_ref,
            orchestrator_run_id=command.orchestrator_run_id,
            generated_count=len(generated),
            deduplicated_count=deduplicated,
            grouped_count=grouped_count,
            published_event_ids=event_ids,
        )
