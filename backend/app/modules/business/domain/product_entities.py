from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.modules.business.domain.product_errors import InvalidProductStateError
from app.modules.business.domain.product_value_objects import (
    ProductExternalReference,
    ProductPricing,
    ProductStatus,
    normalize_sku,
)


@dataclass(slots=True)
class ProductAggregate:
    product_id: str
    company_id: str
    sku: str
    name: str
    category: str | None
    unit_of_measure: str
    status: ProductStatus
    pricing: ProductPricing
    tax_profile_ref: str | None
    external_refs: tuple[ProductExternalReference, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        company_id: str,
        sku: str,
        name: str,
        category: str | None,
        unit_of_measure: str,
        status: ProductStatus,
        default_cost: Decimal,
        default_price: Decimal,
        tax_profile_ref: str | None,
        external_refs: tuple[ProductExternalReference, ...],
    ) -> "ProductAggregate":
        product = cls(
            product_id=str(uuid4()),
            company_id=company_id,
            sku=normalize_sku(sku),
            name=name.strip(),
            category=category.strip() if category else None,
            unit_of_measure=unit_of_measure.strip().upper(),
            status=status,
            pricing=ProductPricing(default_cost=default_cost, default_price=default_price),
            tax_profile_ref=tax_profile_ref.strip() if tax_profile_ref else None,
            external_refs=external_refs,
        )
        product.assert_invariants()
        return product

    def assert_invariants(self) -> None:
        if not self.company_id.strip():
            raise InvalidProductStateError("company_id is required")
        if not self.sku.strip():
            raise InvalidProductStateError("sku is required")
        if not self.name.strip():
            raise InvalidProductStateError("name is required")
        if not self.unit_of_measure.strip():
            raise InvalidProductStateError("unit_of_measure is required")
        if self.pricing.default_cost < Decimal("0"):
            raise InvalidProductStateError("default_cost cannot be negative")
        if self.pricing.default_price < Decimal("0"):
            raise InvalidProductStateError("default_price cannot be negative")

    def update(
        self,
        sku: str,
        name: str,
        category: str | None,
        unit_of_measure: str,
        status: ProductStatus,
        default_cost: Decimal,
        default_price: Decimal,
        tax_profile_ref: str | None,
        external_refs: tuple[ProductExternalReference, ...],
    ) -> None:
        self.sku = normalize_sku(sku)
        self.name = name.strip()
        self.category = category.strip() if category else None
        self.unit_of_measure = unit_of_measure.strip().upper()
        self.status = status
        self.pricing = ProductPricing(default_cost=default_cost, default_price=default_price)
        self.tax_profile_ref = tax_profile_ref.strip() if tax_profile_ref else None
        self.external_refs = external_refs
        self.updated_at = datetime.now(timezone.utc)
        self.assert_invariants()
