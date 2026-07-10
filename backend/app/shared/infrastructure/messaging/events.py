from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True)
class IntegrationEvent:
    topic: str
    payload: dict
    event_id: str = ""
    occurred_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = str(uuid4())
        if self.occurred_at is None:
            self.occurred_at = datetime.now(timezone.utc)
