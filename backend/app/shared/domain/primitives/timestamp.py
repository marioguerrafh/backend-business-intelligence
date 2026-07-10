from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True, frozen=True)
class Timestamp:
    value: datetime

    @classmethod
    def now(cls) -> "Timestamp":
        return cls(value=datetime.now(timezone.utc))
