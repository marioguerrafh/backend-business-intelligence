from app.modules.rule.application.use_case import ExecuteRulesUseCase
from app.modules.rule.infrastructure.repositories import SqlAlchemyRuleRepository
from app.modules.rule.infrastructure.rule_catalog_yaml import YamlRuleCatalogReader


def build_rule_engine_use_case(session) -> ExecuteRulesUseCase:
    return ExecuteRulesUseCase(
        repository=SqlAlchemyRuleRepository(session=session),
        catalog_reader=YamlRuleCatalogReader(),
    )
