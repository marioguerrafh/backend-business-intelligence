from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.executive_score.infrastructure.container import build_executive_score_use_case
from app.modules.insight.infrastructure.container import build_insight_engine_use_case
from app.modules.kpi.infrastructure.container import build_kpi_orchestrator_use_case
from app.modules.pipeline.application.pipeline_coordinator import PipelineCoordinator
from app.modules.pipeline.application.pipeline_event_publisher import PipelineEventPublisher
from app.modules.pipeline.application.pipeline_executor import PipelineExecutor
from app.modules.pipeline.application.pipeline_service import PipelineService
from app.modules.pipeline.infrastructure.repositories import PipelineRepository
from app.modules.recommendation.infrastructure.container import build_recommendation_engine_use_case
from app.modules.rule.infrastructure.container import build_rule_engine_use_case
from app.modules.summary.infrastructure.container import build_summary_container


@dataclass(slots=True)
class PipelineContainer:
    service: PipelineService
    coordinator: PipelineCoordinator


def build_pipeline_container(session: Session) -> PipelineContainer:
    repository = PipelineRepository(session=session)
    executor = PipelineExecutor(
        kpi_orchestrator=build_kpi_orchestrator_use_case(session),
        rule_engine=build_rule_engine_use_case(session),
        recommendation_engine=build_recommendation_engine_use_case(session),
        insight_engine=build_insight_engine_use_case(session),
        executive_score_engine=build_executive_score_use_case(session),
        summary_service=build_summary_container(session).service,
    )
    service = PipelineService(
        repository=repository,
        executor=executor,
        event_publisher=PipelineEventPublisher(repository=repository),
    )
    return PipelineContainer(
        service=service,
        coordinator=PipelineCoordinator(service=service),
    )
