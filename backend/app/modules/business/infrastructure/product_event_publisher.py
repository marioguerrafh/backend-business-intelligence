from app.modules.business.application.ports.product_event_publisher import ProductEventPublisher
from app.modules.business.domain.product_events import BusinessProductUpserted
from app.shared.infrastructure.messaging.events import IntegrationEvent


class InMemoryProductEventPublisher(ProductEventPublisher):
    def __init__(self) -> None:
        self.events: list[BusinessProductUpserted] = []
        self.integration_events: list[IntegrationEvent] = []

    def publish_product_upserted(self, event: BusinessProductUpserted) -> None:
        self.events.append(event)
        self.integration_events.append(
            IntegrationEvent(
                topic="business.product.upserted",
                payload={
                    "event_id": event.event_id,
                    "occurred_at": event.occurred_at.isoformat(),
                    "company_id": event.company_id,
                    "product_id": event.product_id,
                    "source_system": event.source_system,
                    "source_record_id": event.source_record_id,
                    "canonical_schema_version": event.canonical_schema_version,
                    "event_version": "1.0.0",
                },
            )
        )
