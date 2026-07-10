from app.modules.business.application.ports.event_publisher import BusinessEventPublisher
from app.modules.business.domain.events import BusinessCustomerUpserted
from app.shared.infrastructure.messaging.events import IntegrationEvent


class InMemoryBusinessEventPublisher(BusinessEventPublisher):
    def __init__(self) -> None:
        self.events: list[BusinessCustomerUpserted] = []
        self.integration_events: list[IntegrationEvent] = []

    def publish_customer_upserted(self, event: BusinessCustomerUpserted) -> None:
        self.events.append(event)
        self.integration_events.append(
            IntegrationEvent(
                topic="business.customer.upserted",
                payload={
                    "event_id": event.event_id,
                    "occurred_at": event.occurred_at.isoformat(),
                    "company_id": event.company_id,
                    "customer_id": event.customer_id,
                    "source_system": event.source_system,
                    "source_record_id": event.source_record_id,
                    "canonical_schema_version": event.canonical_schema_version,
                    "event_version": "1.0.0",
                },
            )
        )
