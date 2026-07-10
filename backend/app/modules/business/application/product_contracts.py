from dataclasses import dataclass
from decimal import Decimal

from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus


@dataclass(slots=True, frozen=True)
class UpsertProductCommand:
    company_id: str
    sku: str
    name: str
    category: str | None
    unit_of_measure: str
    status: ProductStatus
    default_cost: Decimal
    default_price: Decimal
    tax_profile_ref: str | None
    external_refs: tuple[ProductExternalReference, ...]
    source_system: str
    source_record_id: str
    canonical_schema_version: str
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class GetProductQuery:
    company_id: str
    product_id: str
