from abc import ABC, abstractmethod

from app.modules.business.domain.product_events import BusinessProductUpserted


class ProductEventPublisher(ABC):
    @abstractmethod
    def publish_product_upserted(self, event: BusinessProductUpserted) -> None:
        raise NotImplementedError
