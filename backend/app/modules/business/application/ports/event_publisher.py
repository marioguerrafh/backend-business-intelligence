from abc import ABC, abstractmethod

from app.modules.business.domain.events import BusinessCustomerUpserted


class BusinessEventPublisher(ABC):
    @abstractmethod
    def publish_customer_upserted(self, event: BusinessCustomerUpserted) -> None:
        raise NotImplementedError
