from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AuthenticateCommand:
    email: str
    password: str
    company_id: str
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class RefreshCommand:
    refresh_token: str
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class LogoutCommand:
    refresh_token: str
    correlation_id: str | None = None
