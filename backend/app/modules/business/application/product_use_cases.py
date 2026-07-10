import logging
from dataclasses import dataclass

from app.modules.business.application.ports.product_event_publisher import ProductEventPublisher
from app.modules.business.application.ports.product_repository import ProductRepository
from app.modules.business.application.product_contracts import GetProductQuery, UpsertProductCommand
from app.modules.business.domain.product_entities import ProductAggregate
from app.modules.business.domain.product_errors import (
    DuplicateProductSkuError,
    ProductIdempotencyConflictError,
)
from app.modules.business.domain.product_events import BusinessProductUpserted
from app.modules.business.domain.product_value_objects import normalize_sku
from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher
from app.shared.application.idempotency.service import IdempotencyContext, IdempotencyService
from app.shared.domain.errors import NotFoundError


@dataclass(slots=True)
class UpsertProductResult:
    product: ProductAggregate
    event: BusinessProductUpserted | None
    idempotent_replay: bool = False


class UpsertProductUseCase:
    def __init__(
        self,
        repository: ProductRepository,
        publisher: ProductEventPublisher,
        logger: logging.Logger,
        idempotency_service: IdempotencyService,
        payload_hasher: CanonicalPayloadHasher,
    ) -> None:
        self.repository = repository
        self.publisher = publisher
        self.logger = logger
        self.idempotency_service = idempotency_service
        self.payload_hasher = payload_hasher

    def execute(self, command: UpsertProductCommand) -> UpsertProductResult:
        payload_hash = self._payload_hash(command)
        idempotency_context = IdempotencyContext(
            company_id=command.company_id,
            source_system=command.source_system,
            source_record_id=command.source_record_id,
            payload_hash=payload_hash,
        )
        resolution = self.idempotency_service.resolve_replay(
            context=idempotency_context,
            repository=self.repository,
            load_entity=lambda product_id: self.repository.get_by_id(command.company_id, product_id),
            conflict_error=ProductIdempotencyConflictError,
            missing_entity_error_message="idempotency record references missing product",
        )
        if resolution.is_replay:
            existing_product = resolution.entity
            assert existing_product is not None

            self.logger.info(
                "business.product.upsert.idempotent_replay",
                extra={
                    "company_id": command.company_id,
                    "product_id": existing_product.product_id,
                    "source_system": command.source_system,
                    "source_record_id": command.source_record_id,
                    "correlation_id": command.correlation_id,
                },
            )
            return UpsertProductResult(product=existing_product, event=None, idempotent_replay=True)

        target = self._find_existing(command)
        normalized_sku = normalize_sku(command.sku)
        duplicate = self.repository.get_by_sku(command.company_id, normalized_sku)
        if duplicate and (target is None or duplicate.product_id != target.product_id):
            raise DuplicateProductSkuError("sku already exists for this tenant")

        if target is None:
            product = ProductAggregate.create(
                company_id=command.company_id,
                sku=normalized_sku,
                name=command.name,
                category=command.category,
                unit_of_measure=command.unit_of_measure,
                status=command.status,
                default_cost=command.default_cost,
                default_price=command.default_price,
                tax_profile_ref=command.tax_profile_ref,
                external_refs=command.external_refs,
            )
        else:
            target.update(
                sku=normalized_sku,
                name=command.name,
                category=command.category,
                unit_of_measure=command.unit_of_measure,
                status=command.status,
                default_cost=command.default_cost,
                default_price=command.default_price,
                tax_profile_ref=command.tax_profile_ref,
                external_refs=command.external_refs,
            )
            product = target

        self.repository.save(product)
        self.idempotency_service.persist(
            context=idempotency_context,
            repository=self.repository,
            entity_id=product.product_id,
        )

        event = BusinessProductUpserted.create(
            company_id=command.company_id,
            product_id=product.product_id,
            source_system=command.source_system,
            source_record_id=command.source_record_id,
            canonical_schema_version=command.canonical_schema_version,
        )
        self.publisher.publish_product_upserted(event)
        self.logger.info(
            "business.product.upsert.success",
            extra={
                "company_id": command.company_id,
                "product_id": product.product_id,
                "source_system": command.source_system,
                "source_record_id": command.source_record_id,
                "correlation_id": command.correlation_id,
            },
        )
        return UpsertProductResult(product=product, event=event)

    def _find_existing(self, command: UpsertProductCommand) -> ProductAggregate | None:
        for external_ref in command.external_refs:
            found = self.repository.get_by_external_ref(
                company_id=command.company_id,
                source_system=external_ref.source_system,
                external_id=external_ref.external_id,
            )
            if found is not None:
                return found
        return self.repository.get_by_sku(command.company_id, normalize_sku(command.sku))

    def _payload_hash(self, command: UpsertProductCommand) -> str:
        payload = {
            "company_id": command.company_id,
            "sku": normalize_sku(command.sku),
            "name": command.name.strip(),
            "category": command.category.strip() if command.category else None,
            "unit_of_measure": command.unit_of_measure.strip().upper(),
            "status": command.status.value,
            "default_cost": str(command.default_cost),
            "default_price": str(command.default_price),
            "tax_profile_ref": command.tax_profile_ref.strip() if command.tax_profile_ref else None,
            "external_refs": [
                {
                    "source_system": external_ref.source_system,
                    "external_id": external_ref.external_id,
                }
                for external_ref in command.external_refs
            ],
        }
        return self.payload_hasher.hash_payload(payload)


class GetProductUseCase:
    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    def execute(self, query: GetProductQuery) -> ProductAggregate:
        product = self.repository.get_by_id(query.company_id, query.product_id)
        if product is None:
            raise NotFoundError("product not found")
        return product
