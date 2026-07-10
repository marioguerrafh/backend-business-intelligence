from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.business.domain.errors import InvalidCustomerStateError
from app.modules.business.domain.value_objects import (
    BillingAddress,
    ContactChannel,
    CustomerStatus,
    ExternalReference,
    normalize_document_number,
)


@dataclass(slots=True)
class CustomerAggregate:
    customer_id: str
    company_id: str
    legal_name: str
    trade_name: str | None
    document_number: str | None
    status: CustomerStatus
    billing_address: BillingAddress | None
    contacts: tuple[ContactChannel, ...] = field(default_factory=tuple)
    external_refs: tuple[ExternalReference, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        company_id: str,
        legal_name: str,
        trade_name: str | None,
        document_number: str | None,
        status: CustomerStatus,
        billing_address: BillingAddress | None,
        contacts: tuple[ContactChannel, ...],
        external_refs: tuple[ExternalReference, ...],
    ) -> "CustomerAggregate":
        customer = cls(
            customer_id=str(uuid4()),
            company_id=company_id,
            legal_name=legal_name.strip(),
            trade_name=trade_name.strip() if trade_name else None,
            document_number=normalize_document_number(document_number),
            status=status,
            billing_address=billing_address,
            contacts=contacts,
            external_refs=external_refs,
        )
        customer.assert_invariants()
        return customer

    def assert_invariants(self) -> None:
        if not self.company_id.strip():
            raise InvalidCustomerStateError("company_id is required")
        if not self.legal_name.strip():
            raise InvalidCustomerStateError("legal_name is required")
        if self.status == CustomerStatus.ACTIVE and len(self.contacts) == 0:
            raise InvalidCustomerStateError("active customer requires at least one contact")

    def update(
        self,
        legal_name: str,
        trade_name: str | None,
        document_number: str | None,
        status: CustomerStatus,
        billing_address: BillingAddress | None,
        contacts: tuple[ContactChannel, ...],
        external_refs: tuple[ExternalReference, ...],
    ) -> None:
        self.legal_name = legal_name.strip()
        self.trade_name = trade_name.strip() if trade_name else None
        self.document_number = normalize_document_number(document_number)
        self.status = status
        self.billing_address = billing_address
        self.contacts = contacts
        self.external_refs = external_refs
        self.updated_at = datetime.now(timezone.utc)
        self.assert_invariants()
