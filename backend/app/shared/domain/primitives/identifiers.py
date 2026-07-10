from dataclasses import dataclass
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class EntityId:
    value: str

    @classmethod
    def new(cls) -> "EntityId":
        return cls(value=str(uuid4()))


@dataclass(slots=True, frozen=True)
class AggregateId(EntityId):
    pass
