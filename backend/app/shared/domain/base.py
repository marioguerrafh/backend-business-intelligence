from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(slots=True)
class Entity:
    id: UUID


@dataclass(slots=True)
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
    name: str

    @classmethod
    def create(cls, name: str) -> "DomainEvent":
        return cls(event_id=uuid4(), occurred_at=datetime.now(timezone.utc), name=name)
