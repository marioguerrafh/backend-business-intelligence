from dataclasses import dataclass

from app.modules.business.domain.value_objects import BillingAddress, ContactChannel, CustomerStatus, ExternalReference


@dataclass(slots=True, frozen=True)
class UpsertCustomerCommand:
    company_id: str
    legal_name: str
    trade_name: str | None
    document_number: str | None
    status: CustomerStatus
    billing_address: BillingAddress | None
    contacts: tuple[ContactChannel, ...]
    external_refs: tuple[ExternalReference, ...]
    source_system: str
    source_record_id: str
    canonical_schema_version: str
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class GetCustomerQuery:
    company_id: str
    customer_id: str
