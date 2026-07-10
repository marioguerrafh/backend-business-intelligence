from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.modules.auth.domain.entities import RefreshSession, TokenPair


@dataclass(slots=True, frozen=True)
class TokenClaims:
    token_id: str
    token_type: str
    subject: str
    company_id: str
    roles: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    email: str


class TokenService(ABC):
    @abstractmethod
    def issue_token_pair(self, subject: str, email: str, company_id: str, roles: list[str]) -> tuple[TokenPair, RefreshSession]:
        raise NotImplementedError

    @abstractmethod
    def decode_access_token(self, token: str) -> TokenClaims:
        raise NotImplementedError

    @abstractmethod
    def decode_refresh_token(self, token: str) -> TokenClaims:
        raise NotImplementedError
