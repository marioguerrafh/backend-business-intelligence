from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.business.application.ports.customer_repository import CustomerRepository
from app.modules.business.domain.entities import CustomerAggregate
from app.modules.business.domain.value_objects import (
    BillingAddress,
    ContactChannel,
    ContactChannelType,
    CustomerStatus,
    ExternalReference,
    normalize_document_number,
)
from app.modules.business.infrastructure.models import (
    CustomerContactModel,
    CustomerExternalRefModel,
    CustomerIngestionRecordModel,
    CustomerModel,
)
from app.shared.infrastructure.repository.mixins import SqlAlchemyIdempotencyMixin


class SqlAlchemyCustomerRepository(SqlAlchemyIdempotencyMixin, CustomerRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, customer: CustomerAggregate) -> None:
        model = self.session.get(CustomerModel, customer.customer_id)
        is_existing = model is not None
        if model is None:
            model = CustomerModel(customer_id=customer.customer_id)
            self.session.add(model)

        model.company_id = customer.company_id
        model.legal_name = customer.legal_name
        model.trade_name = customer.trade_name
        model.document_number = customer.document_number
        model.status = customer.status.value

        if customer.billing_address is not None:
            model.billing_street = customer.billing_address.street
            model.billing_number = customer.billing_address.number
            model.billing_district = customer.billing_address.district
            model.billing_city = customer.billing_address.city
            model.billing_state = customer.billing_address.state
            model.billing_country = customer.billing_address.country
            model.billing_postal_code = customer.billing_address.postal_code
        else:
            model.billing_street = None
            model.billing_number = None
            model.billing_district = None
            model.billing_city = None
            model.billing_state = None
            model.billing_country = None
            model.billing_postal_code = None

        model.updated_at = datetime.now(timezone.utc)

        # On re-import, remove old child rows first to avoid unique conflicts
        # when the new payload contains the same contact/external ref values.
        if is_existing:
            model.contacts.clear()
            model.external_refs.clear()
            self.session.flush()

        model.contacts = [
            CustomerContactModel(
                contact_id=str(uuid4()),
                customer_id=customer.customer_id,
                channel_type=contact.channel_type.value,
                value=contact.value,
            )
            for contact in customer.contacts
        ]
        model.external_refs = [
            CustomerExternalRefModel(
                external_ref_id=str(uuid4()),
                customer_id=customer.customer_id,
                company_id=customer.company_id,
                source_system=external_ref.source_system,
                external_id=external_ref.external_id,
            )
            for external_ref in customer.external_refs
        ]

    def get_by_id(self, company_id: str, customer_id: str) -> CustomerAggregate | None:
        stmt = select(CustomerModel).where(
            CustomerModel.customer_id == customer_id,
            CustomerModel.company_id == company_id,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_document(self, company_id: str, document_number: str) -> CustomerAggregate | None:
        normalized = normalize_document_number(document_number)
        if normalized is None:
            return None
        stmt = select(CustomerModel).where(
            CustomerModel.company_id == company_id,
            CustomerModel.document_number == normalized,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_external_ref(self, company_id: str, source_system: str, external_id: str) -> CustomerAggregate | None:
        stmt = (
            select(CustomerModel)
            .join(CustomerExternalRefModel, CustomerExternalRefModel.customer_id == CustomerModel.customer_id)
            .where(
                CustomerModel.company_id == company_id,
                CustomerExternalRefModel.company_id == company_id,
                CustomerExternalRefModel.source_system == source_system.lower(),
                CustomerExternalRefModel.external_id == external_id,
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
            model_cls=CustomerIngestionRecordModel,
            company_id=company_id,
            source_system=source_system,
            source_record_id=source_record_id,
            entity_id_field="customer_id",
        )

    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        customer_id: str,
        payload_hash: str,
    ) -> None:
        self._save_idempotency_record(
            model_cls=CustomerIngestionRecordModel,
            company_id=company_id,
            source_system=source_system,
            source_record_id=source_record_id,
            entity_id=customer_id,
            payload_hash=payload_hash,
            entity_id_field="customer_id",
            id_field="ingestion_record_id",
            id_factory=lambda: str(uuid4()),
        )

    def _to_entity(self, model: CustomerModel) -> CustomerAggregate:
        billing = None
        if model.billing_street and model.billing_city and model.billing_state and model.billing_country:
            billing = BillingAddress(
                street=model.billing_street,
                number=model.billing_number,
                district=model.billing_district,
                city=model.billing_city,
                state=model.billing_state,
                country=model.billing_country,
                postal_code=model.billing_postal_code,
            )

        contacts = tuple(
            ContactChannel(
                channel_type=ContactChannelType(contact.channel_type),
                value=contact.value,
            )
            for contact in model.contacts
        )
        external_refs = tuple(
            ExternalReference(source_system=ref.source_system, external_id=ref.external_id)
            for ref in model.external_refs
        )

        return CustomerAggregate(
            customer_id=model.customer_id,
            company_id=model.company_id,
            legal_name=model.legal_name,
            trade_name=model.trade_name,
            document_number=model.document_number,
            status=CustomerStatus(model.status),
            billing_address=billing,
            contacts=contacts,
            external_refs=external_refs,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
