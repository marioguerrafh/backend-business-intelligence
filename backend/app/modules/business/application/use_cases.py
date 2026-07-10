import logging
from dataclasses import dataclass

from app.modules.business.application.contracts import GetCustomerQuery, UpsertCustomerCommand
from app.modules.business.application.ports.customer_repository import CustomerRepository
from app.modules.business.application.ports.event_publisher import BusinessEventPublisher
from app.modules.business.domain.entities import CustomerAggregate
from app.modules.business.domain.errors import (
    DuplicateCustomerDocumentError,
    IdempotencyConflictError,
    TenantMismatchError,
)
from app.modules.business.domain.events import BusinessCustomerUpserted
from app.modules.business.domain.value_objects import normalize_document_number
from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher
from app.shared.application.idempotency.service import IdempotencyContext, IdempotencyService
from app.shared.domain.errors import NotFoundError


@dataclass(slots=True)
class UpsertCustomerResult:
    customer: CustomerAggregate
    event: BusinessCustomerUpserted | None
    idempotent_replay: bool = False


class UpsertCustomerUseCase:
    def __init__(
        self,
        repository: CustomerRepository,
        publisher: BusinessEventPublisher,
        logger: logging.Logger,
        idempotency_service: IdempotencyService,
        payload_hasher: CanonicalPayloadHasher,
    ) -> None:
        self.repository = repository
        self.publisher = publisher
        self.logger = logger
        self.idempotency_service = idempotency_service
        self.payload_hasher = payload_hasher

    def execute(self, command: UpsertCustomerCommand) -> UpsertCustomerResult:
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
            load_entity=lambda customer_id: self.repository.get_by_id(command.company_id, customer_id),
            conflict_error=IdempotencyConflictError,
            missing_entity_error_message="idempotency record references missing customer",
        )
        if resolution.is_replay:
            existing_customer = resolution.entity
            assert existing_customer is not None

            self.logger.info(
                "business.customer.upsert.idempotent_replay",
                extra={
                    "company_id": command.company_id,
                    "customer_id": existing_customer.customer_id,
                    "source_system": command.source_system,
                    "source_record_id": command.source_record_id,
                    "correlation_id": command.correlation_id,
                },
            )
            return UpsertCustomerResult(customer=existing_customer, event=None, idempotent_replay=True)

        target = self._find_existing(command)

        normalized_document = normalize_document_number(command.document_number)
        if normalized_document:
            duplicate = self.repository.get_by_document(command.company_id, normalized_document)
            if duplicate and (target is None or duplicate.customer_id != target.customer_id):
                raise DuplicateCustomerDocumentError("document_number already exists for this tenant")

        if target is None:
            customer = CustomerAggregate.create(
                company_id=command.company_id,
                legal_name=command.legal_name,
                trade_name=command.trade_name,
                document_number=normalized_document,
                status=command.status,
                billing_address=command.billing_address,
                contacts=command.contacts,
                external_refs=command.external_refs,
            )
        else:
            if target.company_id != command.company_id:
                raise TenantMismatchError("customer tenant mismatch")
            target.update(
                legal_name=command.legal_name,
                trade_name=command.trade_name,
                document_number=normalized_document,
                status=command.status,
                billing_address=command.billing_address,
                contacts=command.contacts,
                external_refs=command.external_refs,
            )
            customer = target

        self.repository.save(customer)
        self.idempotency_service.persist(
            context=idempotency_context,
            repository=self.repository,
            entity_id=customer.customer_id,
        )

        event = BusinessCustomerUpserted.create(
            company_id=command.company_id,
            customer_id=customer.customer_id,
            source_system=command.source_system,
            source_record_id=command.source_record_id,
            canonical_schema_version=command.canonical_schema_version,
        )
        self.publisher.publish_customer_upserted(event)
        self.logger.info(
            "business.customer.upsert.success",
            extra={
                "company_id": command.company_id,
                "customer_id": customer.customer_id,
                "source_system": command.source_system,
                "source_record_id": command.source_record_id,
                "correlation_id": command.correlation_id,
            },
        )
        return UpsertCustomerResult(customer=customer, event=event)

    def _find_existing(self, command: UpsertCustomerCommand) -> CustomerAggregate | None:
        for external_ref in command.external_refs:
            found = self.repository.get_by_external_ref(
                company_id=command.company_id,
                source_system=external_ref.source_system,
                external_id=external_ref.external_id,
            )
            if found is not None:
                return found

        normalized_document = normalize_document_number(command.document_number)
        if normalized_document:
            return self.repository.get_by_document(command.company_id, normalized_document)
        return None

    def _payload_hash(self, command: UpsertCustomerCommand) -> str:
        payload = {
            "company_id": command.company_id,
            "legal_name": command.legal_name.strip(),
            "trade_name": command.trade_name.strip() if command.trade_name else None,
            "document_number": normalize_document_number(command.document_number),
            "status": command.status.value,
            "billing_address": {
                "street": command.billing_address.street,
                "number": command.billing_address.number,
                "district": command.billing_address.district,
                "city": command.billing_address.city,
                "state": command.billing_address.state,
                "country": command.billing_address.country,
                "postal_code": command.billing_address.postal_code,
            }
            if command.billing_address
            else None,
            "contacts": [
                {
                    "channel_type": contact.channel_type.value,
                    "value": contact.value,
                }
                for contact in command.contacts
            ],
            "external_refs": [
                {
                    "source_system": external_ref.source_system,
                    "external_id": external_ref.external_id,
                }
                for external_ref in command.external_refs
            ],
        }
        return self.payload_hasher.hash_payload(payload)


class GetCustomerUseCase:
    def __init__(self, repository: CustomerRepository) -> None:
        self.repository = repository

    def execute(self, query: GetCustomerQuery) -> CustomerAggregate:
        customer = self.repository.get_by_id(query.company_id, query.customer_id)
        if customer is None:
            raise NotFoundError("customer not found")
        return customer
