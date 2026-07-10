from pydantic import BaseModel, Field


class ExternalRefRequest(BaseModel):
    source_system: str = Field(min_length=2, max_length=64)
    external_id: str = Field(min_length=1, max_length=255)


class ContactRequest(BaseModel):
    channel_type: str = Field(min_length=3, max_length=32)
    value: str = Field(min_length=1, max_length=255)


class BillingAddressRequest(BaseModel):
    street: str = Field(min_length=1, max_length=255)
    number: str | None = Field(default=None, max_length=32)
    district: str | None = Field(default=None, max_length=120)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=64)
    country: str = Field(min_length=1, max_length=64)
    postal_code: str | None = Field(default=None, max_length=32)


class UpsertCustomerRequest(BaseModel):
    company_id: str = Field(min_length=3, max_length=64)
    legal_name: str = Field(min_length=2, max_length=255)
    trade_name: str | None = Field(default=None, max_length=255)
    document_number: str | None = Field(default=None, max_length=32)
    status: str = Field(min_length=6, max_length=16)
    billing_address: BillingAddressRequest | None = None
    contacts: list[ContactRequest] = Field(default_factory=list)
    external_refs: list[ExternalRefRequest] = Field(default_factory=list)
    source_system: str = Field(min_length=2, max_length=64)
    source_record_id: str = Field(min_length=1, max_length=255)
    canonical_schema_version: str = Field(min_length=1, max_length=32)


class CustomerResponse(BaseModel):
    customer_id: str
    company_id: str
    legal_name: str
    trade_name: str | None
    document_number: str | None
    status: str
    contacts: list[dict[str, str]]
    external_refs: list[dict[str, str]]
