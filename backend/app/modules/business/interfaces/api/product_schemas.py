from decimal import Decimal

from pydantic import BaseModel, Field


class ProductExternalRefRequest(BaseModel):
    source_system: str = Field(min_length=2, max_length=64)
    external_id: str = Field(min_length=1, max_length=255)


class UpsertProductRequest(BaseModel):
    company_id: str = Field(min_length=3, max_length=64)
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    unit_of_measure: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=6, max_length=16)
    default_cost: Decimal = Field(ge=0)
    default_price: Decimal = Field(ge=0)
    tax_profile_ref: str | None = Field(default=None, max_length=120)
    external_refs: list[ProductExternalRefRequest] = Field(default_factory=list)
    source_system: str = Field(min_length=2, max_length=64)
    source_record_id: str = Field(min_length=1, max_length=255)
    canonical_schema_version: str = Field(min_length=1, max_length=32)


class ProductResponse(BaseModel):
    product_id: str
    company_id: str
    sku: str
    name: str
    category: str | None
    unit_of_measure: str
    status: str
    default_cost: str
    default_price: str
    tax_profile_ref: str | None
    external_refs: list[dict[str, str]]
