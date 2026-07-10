from app.shared.domain.errors import DomainError


class AuthError(DomainError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InactiveUserError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class TokenRevokedError(AuthError):
    pass


class TenantAccessDeniedError(AuthError):
    pass


class RoleAccessDeniedError(AuthError):
    pass
