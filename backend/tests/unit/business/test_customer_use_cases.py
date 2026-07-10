import pytest

from app.modules.business.application.contracts import GetCustomerQuery, UpsertCustomerCommand
from app.modules.business.application.ports.customer_repository import CustomerRepository
from app.modules.business.application.use_cases import GetCustomerUseCase, UpsertCustomerUseCase
from app.modules.business.domain.entities import CustomerAggregate
from app.modules.business.domain.errors import DuplicateCustomerDocumentError, IdempotencyConflictError
from app.modules.business.domain.value_objects import ContactChannel, ContactChannelType, CustomerStatus, ExternalReference
from app.modules.business.infrastructure.event_publisher import InMemoryBusinessEventPublisher
from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher
from app.shared.application.idempotency.service import IdempotencyService
from app.shared.domain.errors import NotFoundError


class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self) -> None:
        self.data: dict[str, CustomerAggregate] = {}
        self.idempotency: dict[tuple[str, str, str], tuple[str, str]] = {}

    def save(self, customer: CustomerAggregate) -> None:
        self.data[customer.customer_id] = customer

    def get_by_id(self, company_id: str, customer_id: str) -> CustomerAggregate | None:
        customer = self.data.get(customer_id)
        if customer is None:
            return None
        return customer if customer.company_id == company_id else None

    def get_by_document(self, company_id: str, document_number: str) -> CustomerAggregate | None:
        for customer in self.data.values():
            if customer.company_id == company_id and customer.document_number == document_number:
                return customer
        return None

    def get_by_external_ref(self, company_id: str, source_system: str, external_id: str) -> CustomerAggregate | None:
        for customer in self.data.values():
            if customer.company_id != company_id:
                continue
            for ref in customer.external_refs:
                if ref.source_system == source_system and ref.external_id == external_id:
                    return customer
        return None

    def get_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
    ) -> tuple[str, str] | None:
        return self.idempotency.get((company_id, source_system.lower(), source_record_id))

    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        customer_id: str,
        payload_hash: str,
    ) -> None:
        self.idempotency[(company_id, source_system.lower(), source_record_id)] = (customer_id, payload_hash)


def _command(document_number: str, external_id: str, source_record_id: str | None = None) -> UpsertCustomerCommand:
    return UpsertCustomerCommand(
        company_id="cmp_acme",
        legal_name="ACME LTDA",
        trade_name="ACME",
        document_number=document_number,
        status=CustomerStatus.ACTIVE,
        billing_address=None,
        contacts=(ContactChannel(channel_type=ContactChannelType.EMAIL, value="financeiro@acme.com"),),
        external_refs=(ExternalReference(source_system="omie", external_id=external_id),),
        source_system="omie",
        source_record_id=source_record_id or external_id,
        canonical_schema_version="1.0.0",
    )


def test_upsert_customer_publishes_event() -> None:
    repository = InMemoryCustomerRepository()
    publisher = InMemoryBusinessEventPublisher()

    use_case = UpsertCustomerUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )
    result = use_case.execute(_command("12345678000199", "EXT-1"))

    assert result.customer.customer_id
    assert len(publisher.events) == 1
    assert publisher.events[0].customer_id == result.customer.customer_id


def test_upsert_customer_rejects_duplicate_document() -> None:
    repository = InMemoryCustomerRepository()
    publisher = InMemoryBusinessEventPublisher()
    use_case = UpsertCustomerUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    use_case.execute(_command("12345678000199", "EXT-1"))
    use_case.execute(_command("98765432000110", "EXT-2"))

    with pytest.raises(DuplicateCustomerDocumentError):
        use_case.execute(_command("12.345.678/0001-99", "EXT-2", source_record_id="SRC-NEW"))


def test_get_customer_not_found() -> None:
    repository = InMemoryCustomerRepository()
    use_case = GetCustomerUseCase(repository=repository)

    with pytest.raises(NotFoundError):
        use_case.execute(GetCustomerQuery(company_id="cmp_acme", customer_id="missing"))


def test_upsert_customer_idempotent_replay_returns_same_customer_without_event() -> None:
    repository = InMemoryCustomerRepository()
    publisher = InMemoryBusinessEventPublisher()
    use_case = UpsertCustomerUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    first = use_case.execute(_command("12345678000199", "EXT-123"))
    second = use_case.execute(_command("12345678000199", "EXT-123"))

    assert second.customer.customer_id == first.customer.customer_id
    assert second.idempotent_replay is True
    assert second.event is None
    assert len(publisher.events) == 1


def test_upsert_customer_idempotency_conflict_when_payload_changes() -> None:
    repository = InMemoryCustomerRepository()
    publisher = InMemoryBusinessEventPublisher()
    use_case = UpsertCustomerUseCase(
        repository=repository,
        publisher=publisher,
        logger=__import__("logging").getLogger("test.business"),
        idempotency_service=IdempotencyService(),
        payload_hasher=CanonicalPayloadHasher(),
    )

    use_case.execute(_command("12345678000199", "EXT-123"))

    with pytest.raises(IdempotencyConflictError):
        use_case.execute(_command("98765432000110", "EXT-123"))
