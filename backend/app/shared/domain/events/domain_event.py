from dataclasses import dataclass

from app.shared.domain.primitives.correlation_id import CorrelationId
from app.shared.domain.primitives.identifiers import EntityId
from app.shared.domain.primitives.timestamp import Timestamp


@dataclass(slots=True, frozen=True)
class DomainEvent:
    event_id: EntityId
    occurred_at: Timestamp
    correlation_id: CorrelationId | None = None
