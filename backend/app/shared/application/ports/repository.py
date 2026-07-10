from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def add(self, entity: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, entity_id: str) -> T | None:
        raise NotImplementedError
