from typing import Protocol

from app.shared.infrastructure.messaging.events import IntegrationEvent


class EventDispatcher(Protocol):
    def dispatch(self, event: IntegrationEvent) -> None:
        raise NotImplementedError

    def dispatch_batch(self, events: list[IntegrationEvent]) -> None:
        raise NotImplementedError
