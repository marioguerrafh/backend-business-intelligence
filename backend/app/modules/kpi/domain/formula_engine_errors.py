class FormulaEngineError(Exception):
    """Base error for formula engine failures."""


class FormulaSyntaxError(FormulaEngineError):
    pass


class FormulaValidationError(FormulaEngineError):
    pass


class FormulaDependencyError(FormulaEngineError):
    pass


class FormulaExecutionError(FormulaEngineError):
    pass
