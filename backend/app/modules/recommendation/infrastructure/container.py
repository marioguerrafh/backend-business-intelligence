from app.modules.recommendation.application.recommendation_builder import RecommendationBuilder
from app.modules.recommendation.application.recommendation_publisher import RecommendationPublisher
from app.modules.recommendation.application.recommendation_prioritizer import RecommendationPrioritizer
from app.modules.recommendation.application.recommendation_service import RecommendationService
from app.modules.recommendation.application.use_cases import GenerateRecommendationsUseCase
from app.modules.recommendation.infrastructure.recommendation_catalog_yaml import YamlRecommendationCatalogReader
from app.modules.recommendation.infrastructure.repositories import SqlAlchemyRecommendationRepository


def build_recommendation_engine_use_case(session) -> GenerateRecommendationsUseCase:
    repository = SqlAlchemyRecommendationRepository(session=session)
    service = RecommendationService(
        repository=repository,
        builder=RecommendationBuilder(),
        prioritizer=RecommendationPrioritizer(),
        publisher=RecommendationPublisher(repository=repository),
    )
    return GenerateRecommendationsUseCase(
        catalog_reader=YamlRecommendationCatalogReader(),
        service=service,
    )
