class RecommendationEngineError(Exception):
    """Base error for recommendation engine."""


class RecommendationCatalogValidationError(RecommendationEngineError):
    """Raised when recommendation DSL content is invalid."""


class RecommendationEvaluationError(RecommendationEngineError):
    """Raised when recommendation evaluation fails."""
