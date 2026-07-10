from decimal import Decimal

import pytest

from app.modules.business.application.ports.product_repository import ProductRepository
from app.modules.business.application.product_contracts import GetProductQuery, UpsertProductCommand
from app.modules.business.application.product_use_cases import GetProductUseCase, UpsertProductUseCase
from app.modules.business.domain.product_entities import ProductAggregate
from app.modules.business.domain.product_errors import DuplicateProductSkuError, ProductIdempotencyConflictError
from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus
from app.modules.business.infrastructure.product_event_publisher import InMemoryProductEventPublisher
from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher
from app.shared.application.idempotency.service import IdempotencyService
from app.shared.domain.errors import NotFoundError


class InMemoryProductRepository(ProductRepository):
    def __init__(self) -> None:
        self.data: dict[str, ProductAggregate] = {}
        self.idempotency: dict[tuple[str, str, str], tuple[str, str]] = {}

    def save(self, product: ProductAggregate) -> None:
        self.data[product.product_id] = product

    def get_by_id(self, company_id: str, product_id: str) -> ProductAggregate | None:
        product = self.data.get(product_id)
        if product is None:
            return None
        return product if product.company_id == company_id else None

    def get_by_sku(self, company_id: str, sku: str) -> ProductAggregate | None:
        normalized = sku.strip().upper()
        for product in self.data.values():
            if product.company_id == company_id and product.sku == normalized:
                return product
        return None

    def get_by_external_ref(self, company_id: str, source_system: str, external_id: str) -> ProductAggregate | None:
        for product in self.data.values():
            if product.company_id != company_id:
                continue
            for ref in product.external_refs:
                if ref.source_system == source_system and ref.external_id == external_id:
                    return product
        return None

    def get_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
    ) -> tuple[str, str] | None:
        return self.idempotency.get((company_id, source_system.lower(), source_record_id))

    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        product_id: str,
        payload_hash: str,
    ) -> None:
        self.idempotency[(company_id, source_system.lower(), source_record_id)] = (product_id, payload_hash)


def _command(sku: str, external_id: str, source_record_id: str | None = None) -> UpsertProductCommand:
    return UpsertProductCommand(
        company_id="cmp_acme",
        sku=sku,
        name="Produto A",
        category="Categoria",
        unit_of_measure="UN",
        status=ProductStatus.ACTIVE,
        default_cost=Decimal("10"),
        default_price=Decimal("20"),
        tax_profile_ref=None,
        external_refs=(ProductExternalReference(source_system="omie", external_id=external_id),),
        source_system="omie",
        source_record_id=source_record_id or external_id,
        canonical_schema_version="1.0.0",
    )


def test_upsert_product_publishes_event() -> None:
    repository = InMemoryProductRepository()
    publisher = InMemoryProductEventPublisher()
    use_case = UpsertProductUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business.product"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    result = use_case.execute(_command("prd-1", "EXT-1"))

    assert result.product.product_id
    assert len(publisher.events) == 1


def test_upsert_product_rejects_duplicate_sku() -> None:
    repository = InMemoryProductRepository()
    publisher = InMemoryProductEventPublisher()
    use_case = UpsertProductUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business.product"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    use_case.execute(_command("PRD-1", "EXT-1"))
    use_case.execute(_command("PRD-2", "EXT-2"))

    with pytest.raises(DuplicateProductSkuError):
        use_case.execute(_command("PRD-1", "EXT-2", source_record_id="SRC-NEW"))


def test_upsert_product_idempotent_replay() -> None:
    repository = InMemoryProductRepository()
    publisher = InMemoryProductEventPublisher()
    use_case = UpsertProductUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business.product"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    first = use_case.execute(_command("PRD-1", "EXT-900", source_record_id="SRC-900"))
    replay = use_case.execute(_command("PRD-1", "EXT-900", source_record_id="SRC-900"))

    assert replay.idempotent_replay is True
    assert replay.product.product_id == first.product.product_id
    assert replay.event is None
    assert len(publisher.events) == 1


def test_upsert_product_idempotency_conflict() -> None:
    repository = InMemoryProductRepository()
    publisher = InMemoryProductEventPublisher()
    use_case = UpsertProductUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business.product"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    use_case.execute(_command("PRD-1", "EXT-910", source_record_id="SRC-910"))

    with pytest.raises(ProductIdempotencyConflictError):
        use_case.execute(_command("PRD-2", "EXT-910", source_record_id="SRC-910"))


def test_get_product_not_found() -> None:
    repository = InMemoryProductRepository()
    use_case = GetProductUseCase(repository=repository)

    with pytest.raises(NotFoundError):
        use_case.execute(GetProductQuery(company_id="cmp_acme", product_id="missing"))
