class RuleEngineError(Exception):
    """Base error for rule engine failures."""


class RuleCatalogValidationError(RuleEngineError):
    pass


class RuleConditionSyntaxError(RuleEngineError):
    pass


class RuleEvaluationError(RuleEngineError):
    pass
