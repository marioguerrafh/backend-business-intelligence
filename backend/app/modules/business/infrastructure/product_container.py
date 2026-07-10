import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.business.application.product_use_cases import GetProductUseCase, UpsertProductUseCase
from app.modules.business.infrastructure.product_event_publisher import InMemoryProductEventPublisher
from app.modules.business.infrastructure.product_repositories import SqlAlchemyProductRepository
from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher
from app.shared.application.idempotency.service import IdempotencyService


@dataclass(slots=True)
class ProductContainer:
    upsert_product: UpsertProductUseCase
    get_product: GetProductUseCase
    publisher: InMemoryProductEventPublisher


def build_product_container(session: Session) -> ProductContainer:
    logger = logging.getLogger("app.business.product")
    repository = SqlAlchemyProductRepository(session=session)
    publisher = InMemoryProductEventPublisher()
    idempotency_service = IdempotencyService()
    payload_hasher = CanonicalPayloadHasher()
    return ProductContainer(
        upsert_product=UpsertProductUseCase(
            repository=repository,
            publisher=publisher,
            logger=logger,
            idempotency_service=idempotency_service,
            payload_hasher=payload_hasher,
        ),
        get_product=GetProductUseCase(repository=repository),
        publisher=publisher,
    )
