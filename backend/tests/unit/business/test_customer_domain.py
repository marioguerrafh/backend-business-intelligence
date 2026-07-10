import pytest

from app.modules.business.domain.entities import CustomerAggregate
from app.modules.business.domain.errors import InvalidCustomerStateError
from app.modules.business.domain.value_objects import (
    BillingAddress,
    ContactChannel,
    ContactChannelType,
    CustomerStatus,
    ExternalReference,
)


def test_active_customer_requires_contact() -> None:
    with pytest.raises(InvalidCustomerStateError):
        CustomerAggregate.create(
            company_id="cmp_acme",
            legal_name="ACME LTDA",
            trade_name=None,
            document_number="12.345.678/0001-99",
            status=CustomerStatus.ACTIVE,
            billing_address=None,
            contacts=tuple(),
            external_refs=(ExternalReference(source_system="omie", external_id="123"),),
        )


def test_customer_create_normalizes_document() -> None:
    customer = CustomerAggregate.create(
        company_id="cmp_acme",
        legal_name="ACME LTDA",
        trade_name="ACME",
        document_number="12.345.678/0001-99",
        status=CustomerStatus.ACTIVE,
        billing_address=BillingAddress(
            street="Rua 1",
            number="10",
            district="Centro",
            city="Sao Paulo",
            state="SP",
            country="BR",
            postal_code="01000-000",
        ),
        contacts=(
            ContactChannel(channel_type=ContactChannelType.EMAIL, value="financeiro@acme.com"),
        ),
        external_refs=(ExternalReference(source_system="omie", external_id="123"),),
    )

    assert customer.document_number == "12345678000199"
    assert customer.status == CustomerStatus.ACTIVE
