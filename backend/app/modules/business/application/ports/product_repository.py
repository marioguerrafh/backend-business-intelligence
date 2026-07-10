from abc import ABC, abstractmethod

from app.modules.business.domain.product_entities import ProductAggregate


class ProductRepository(ABC):
    @abstractmethod
    def save(self, product: ProductAggregate) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, company_id: str, product_id: str) -> ProductAggregate | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_sku(self, company_id: str, sku: str) -> ProductAggregate | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_external_ref(
        self,
        company_id: str,
        source_system: str,
        external_id: str,
    ) -> ProductAggregate | None:
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
        product_id: str,
        payload_hash: str,
    ) -> None:
        raise NotImplementedError
