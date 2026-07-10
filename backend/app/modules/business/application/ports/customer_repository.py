from abc import ABC, abstractmethod

from app.modules.business.domain.entities import CustomerAggregate


class CustomerRepository(ABC):
    @abstractmethod
    def save(self, customer: CustomerAggregate) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, company_id: str, customer_id: str) -> CustomerAggregate | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_document(self, company_id: str, document_number: str) -> CustomerAggregate | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_external_ref(
        self,
        company_id: str,
        source_system: str,
        external_id: str,
    ) -> CustomerAggregate | None:
        raise NotImplementedError

    @abstractmethod
    def get_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
    ) -> tuple[str, str] | None:
        raise NotImplementedError

    @abstractmethod
    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        customer_id: str,
        payload_hash: str,
    ) -> None:
        raise NotImplementedError
