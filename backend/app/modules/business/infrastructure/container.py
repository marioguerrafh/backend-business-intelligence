import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.business.application.use_cases import GetCustomerUseCase, UpsertCustomerUseCase
from app.modules.business.infrastructure.event_publisher import InMemoryBusinessEventPublisher
from app.modules.business.infrastructure.repositories import SqlAlchemyCustomerRepository
from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher
from app.shared.application.idempotency.service import IdempotencyService


@dataclass(slots=True)
class CustomerContainer:
    upsert_customer: UpsertCustomerUseCase
    get_customer: GetCustomerUseCase
    publisher: InMemoryBusinessEventPublisher


def build_customer_container(session: Session) -> CustomerContainer:
    logger = logging.getLogger("app.business.customer")
    repository = SqlAlchemyCustomerRepository(session=session)
    publisher = InMemoryBusinessEventPublisher()
    idempotency_service = IdempotencyService()
    payload_hasher = CanonicalPayloadHasher()
    return CustomerContainer(
        upsert_customer=UpsertCustomerUseCase(
            repository=repository,
            publisher=publisher,
            logger=logger,
            idempotency_service=idempotency_service,
            payload_hasher=payload_hasher,
        ),
        get_customer=GetCustomerUseCase(repository=repository),
        publisher=publisher,
    )
