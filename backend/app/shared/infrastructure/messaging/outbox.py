from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True, frozen=True)
class OutboxMessage:
    message_id: str
    topic: str
    payload: dict
    occurred_at: datetime


class Outbox(Protocol):
    def enqueue(self, message: OutboxMessage) -> None:
        raise NotImplementedError

    def dequeue_batch(self, batch_size: int) -> list[OutboxMessage]:
        raise NotImplementedError

    def mark_dispatched(self, message_id: str) -> None:
        raise NotImplementedError
