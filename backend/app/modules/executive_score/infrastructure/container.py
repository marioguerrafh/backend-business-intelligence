from app.modules.executive_score.application.score_calculator import ExecutiveScoreCalculator
from app.modules.executive_score.application.use_case import CalculateExecutiveScoreUseCase
from app.modules.executive_score.infrastructure.repositories import SqlAlchemyExecutiveScoreRepository


def build_executive_score_use_case(session) -> CalculateExecutiveScoreUseCase:
    return CalculateExecutiveScoreUseCase(
        repository=SqlAlchemyExecutiveScoreRepository(session=session),
        calculator=ExecutiveScoreCalculator(),
    )
