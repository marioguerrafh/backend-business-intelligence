from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.business.application.ports.product_repository import ProductRepository
from app.modules.business.domain.product_entities import ProductAggregate
from app.modules.business.domain.product_value_objects import (
    ProductExternalReference,
    ProductPricing,
    ProductStatus,
    normalize_sku,
)
from app.modules.business.infrastructure.models import (
    ProductExternalRefModel,
    ProductIngestionRecordModel,
    ProductModel,
)
from app.shared.infrastructure.repository.mixins import SqlAlchemyIdempotencyMixin


class SqlAlchemyProductRepository(SqlAlchemyIdempotencyMixin, ProductRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, product: ProductAggregate) -> None:
        model = self.session.get(ProductModel, product.product_id)
        if model is None:
            model = ProductModel(product_id=product.product_id)
            self.session.add(model)

        model.company_id = product.company_id
        model.sku = product.sku
        model.name = product.name
        model.category = product.category
        model.unit_of_measure = product.unit_of_measure
        model.status = product.status.value
        model.default_cost = str(product.pricing.default_cost)
        model.default_price = str(product.pricing.default_price)
        model.tax_profile_ref = product.tax_profile_ref
        model.updated_at = datetime.now(timezone.utc)

        model.external_refs = [
            ProductExternalRefModel(
                external_ref_id=str(uuid4()),
                product_id=product.product_id,
                company_id=product.company_id,
                source_system=external_ref.source_system,
                external_id=external_ref.external_id,
            )
            for external_ref in product.external_refs
        ]

    def get_by_id(self, company_id: str, product_id: str) -> ProductAggregate | None:
        stmt = select(ProductModel).where(
            ProductModel.product_id == product_id,
            ProductModel.company_id == company_id,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_sku(self, company_id: str, sku: str) -> ProductAggregate | None:
        stmt = select(ProductModel).where(
            ProductModel.company_id == company_id,
            ProductModel.sku == normalize_sku(sku),
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_external_ref(self, company_id: str, source_system: str, external_id: str) -> ProductAggregate | None:
        stmt = (
            select(ProductModel)
            .join(ProductExternalRefModel, ProductExternalRefModel.product_id == ProductModel.product_id)
            .where(
                ProductModel.company_id == company_id,
                ProductExternalRefModel.company_id == company_id,
                ProductExternalRefModel.source_system == source_system.lower(),
                ProductExternalRefModel.external_id == external_id,
            )
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def get_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
    ) -> tuple[str, str] | None:
        return self._get_idempotency_record(
            model_cls=ProductIngestionRecordModel,
            company_id=company_id,
            source_system=source_system,
            source_record_id=source_record_id,
            entity_id_field="product_id",
        )

    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        product_id: str,
        payload_hash: str,
    ) -> None:
        self._save_idempotency_record(
            model_cls=ProductIngestionRecordModel,
            company_id=company_id,
            source_system=source_system,
            source_record_id=source_record_id,
            entity_id=product_id,
            payload_hash=payload_hash,
            entity_id_field="product_id",
            id_field="ingestion_record_id",
            id_factory=lambda: str(uuid4()),
        )

    def _to_entity(self, model: ProductModel) -> ProductAggregate:
        return ProductAggregate(
            product_id=model.product_id,
            company_id=model.company_id,
            sku=model.sku,
            name=model.name,
            category=model.category,
            unit_of_measure=model.unit_of_measure,
            status=ProductStatus(model.status),
            pricing=ProductPricing(
                default_cost=Decimal(model.default_cost),
                default_price=Decimal(model.default_price),
            ),
            tax_profile_ref=model.tax_profile_ref,
            external_refs=tuple(
                ProductExternalReference(source_system=ref.source_system, external_id=ref.external_id)
                for ref in model.external_refs
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
