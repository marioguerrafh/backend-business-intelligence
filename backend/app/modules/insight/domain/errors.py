class InsightEngineError(Exception):
    """Base error for insight engine."""


class InsightCatalogValidationError(InsightEngineError):
    """Raised when AI prompt DSL content is invalid."""


class InsightGenerationError(InsightEngineError):
    """Raised when insight template generation fails."""
