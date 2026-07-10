from abc import ABC, abstractmethod

from app.modules.auth.domain.entities import UserAccount


class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserAccount | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: str) -> UserAccount | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_company(self, company_id: str) -> list[UserAccount]:
        raise NotImplementedError
