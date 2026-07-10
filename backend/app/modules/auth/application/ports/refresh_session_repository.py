from abc import ABC, abstractmethod

from app.modules.auth.domain.entities import RefreshSession


class RefreshSessionRepository(ABC):
    @abstractmethod
    def save(self, session: RefreshSession) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, token_id: str) -> RefreshSession | None:
        raise NotImplementedError

    @abstractmethod
    def revoke(self, token_id: str, replaced_by: str | None = None) -> None:
        raise NotImplementedError
