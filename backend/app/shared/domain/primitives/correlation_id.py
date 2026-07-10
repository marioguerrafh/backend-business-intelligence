from dataclasses import dataclass
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class CorrelationId:
    value: str

    @classmethod
    def from_header(cls, value: str | None) -> "CorrelationId":
        if value and value.strip():
            return cls(value=value.strip())
        return cls.new()

    @classmethod
    def new(cls) -> "CorrelationId":
        return cls(value=str(uuid4()))
