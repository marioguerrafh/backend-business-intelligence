from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.summary.application.summary_builder import SummaryBuilder
from app.modules.summary.application.summary_cache import InMemorySummaryCache
from app.modules.summary.application.summary_projection import SummaryProjection
from app.modules.summary.application.summary_service import SummaryService
from app.modules.summary.infrastructure.repositories import SqlAlchemySummaryRepository

_summary_cache = InMemorySummaryCache(ttl_seconds=120)


@dataclass(slots=True)
class SummaryContainer:
    service: SummaryService


def build_summary_container(session: Session) -> SummaryContainer:
    repository = SqlAlchemySummaryRepository(session=session)
    service = SummaryService(
        repository=repository,
        builder=SummaryBuilder(),
        projection=SummaryProjection(),
        cache=_summary_cache,
    )
    return SummaryContainer(service=service)
