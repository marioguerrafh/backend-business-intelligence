from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


@dataclass(slots=True, frozen=True)
class CompanyMembership:
    company_id: str
    roles: frozenset[Role]


@dataclass(slots=True)
class UserAccount:
    user_id: str
    email: str
    password_hash: str
    is_active: bool
    memberships: tuple[CompanyMembership, ...]

    def roles_for_company(self, company_id: str) -> list[str]:
        for membership in self.memberships:
            if membership.company_id == company_id:
                return sorted(role.value for role in membership.roles)
        return []

    def belongs_to_company(self, company_id: str) -> bool:
        return bool(self.roles_for_company(company_id))


@dataclass(slots=True, frozen=True)
class AuthPrincipal:
    user_id: str
    email: str
    company_id: str
    roles: tuple[str, ...]


@dataclass(slots=True)
class RefreshSession:
    token_id: str
    user_id: str
    company_id: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    replaced_by_token_id: str | None = None

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
