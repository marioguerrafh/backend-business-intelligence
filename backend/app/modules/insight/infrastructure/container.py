from app.modules.insight.application.template_renderer import InsightTemplateRenderer
from app.modules.insight.application.use_cases import GenerateInsightsUseCase
from app.modules.insight.infrastructure.prompt_catalog_yaml import YamlPromptCatalogReader
from app.modules.insight.infrastructure.repositories import SqlAlchemyInsightRepository


def build_insight_engine_use_case(session) -> GenerateInsightsUseCase:
    return GenerateInsightsUseCase(
        repository=SqlAlchemyInsightRepository(session=session),
        prompt_catalog=YamlPromptCatalogReader(),
        renderer=InsightTemplateRenderer(),
    )
