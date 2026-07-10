import logging

from app.modules.auth.application.ports.clock import Clock
from app.modules.auth.application.ports.password_hasher import PasswordHasher
from app.modules.auth.application.ports.refresh_session_repository import RefreshSessionRepository
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.application.ports.user_repository import UserRepository
from app.modules.auth.application.schemas import AuthenticateCommand, LogoutCommand, RefreshCommand
from app.modules.auth.domain.entities import AuthPrincipal, TokenPair
from app.modules.auth.domain.errors import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RoleAccessDeniedError,
    TenantAccessDeniedError,
    TokenRevokedError,
)


class AuthenticateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        refresh_repository: RefreshSessionRepository,
        logger: logging.Logger,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.refresh_repository = refresh_repository
        self.logger = logger

    def execute(self, command: AuthenticateCommand) -> TokenPair:
        user = self.user_repository.get_by_email(command.email.lower())
        if user is None:
            raise InvalidCredentialsError("invalid credentials")

        if not user.is_active:
            raise InactiveUserError("user is inactive")

        if not self.password_hasher.verify(command.password, user.password_hash):
            raise InvalidCredentialsError("invalid credentials")

        if not user.belongs_to_company(command.company_id):
            raise TenantAccessDeniedError("user does not belong to the requested company")

        roles = user.roles_for_company(command.company_id)
        token_pair, refresh_session = self.token_service.issue_token_pair(
            subject=user.user_id,
            email=user.email,
            company_id=command.company_id,
            roles=roles,
        )
        self.refresh_repository.save(refresh_session)
        self.logger.info(
            "auth.login.success",
            extra={
                "company_id": command.company_id,
                "user_id": user.user_id,
                "correlation_id": command.correlation_id,
            },
        )
        return token_pair


class RefreshSessionUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
        refresh_repository: RefreshSessionRepository,
        clock: Clock,
        logger: logging.Logger,
    ) -> None:
        self.user_repository = user_repository
        self.token_service = token_service
        self.refresh_repository = refresh_repository
        self.clock = clock
        self.logger = logger

    def execute(self, command: RefreshCommand) -> TokenPair:
        claims = self.token_service.decode_refresh_token(command.refresh_token)
        session = self.refresh_repository.get(claims.token_id)

        if session is None:
            raise InvalidTokenError("refresh token session not found")
        if not session.is_active(self.clock.now()):
            raise TokenRevokedError("refresh token is expired or revoked")

        user = self.user_repository.get_by_id(claims.subject)
        if user is None:
            raise InvalidTokenError("user not found")
        if not user.is_active:
            raise InactiveUserError("user is inactive")
        if not user.belongs_to_company(claims.company_id):
            raise TenantAccessDeniedError("user does not belong to token tenant")

        roles = user.roles_for_company(claims.company_id)
        token_pair, new_session = self.token_service.issue_token_pair(
            subject=user.user_id,
            email=user.email,
            company_id=claims.company_id,
            roles=roles,
        )
        self.refresh_repository.revoke(claims.token_id, replaced_by=new_session.token_id)
        self.refresh_repository.save(new_session)

        self.logger.info(
            "auth.refresh.success",
            extra={
                "company_id": claims.company_id,
                "user_id": user.user_id,
                "correlation_id": command.correlation_id,
            },
        )
        return token_pair


class LogoutUseCase:
    def __init__(self, token_service: TokenService, refresh_repository: RefreshSessionRepository) -> None:
        self.token_service = token_service
        self.refresh_repository = refresh_repository

    def execute(self, command: LogoutCommand) -> None:
        claims = self.token_service.decode_refresh_token(command.refresh_token)
        self.refresh_repository.revoke(claims.token_id)


class GetCurrentPrincipalUseCase:
    def __init__(self, token_service: TokenService) -> None:
        self.token_service = token_service

    def execute(self, access_token: str) -> AuthPrincipal:
        claims = self.token_service.decode_access_token(access_token)
        return AuthPrincipal(
            user_id=claims.subject,
            email=claims.email,
            company_id=claims.company_id,
            roles=claims.roles,
        )


class ListCompanyUsersUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def execute(self, principal: AuthPrincipal) -> list[AuthPrincipal]:
        users = self.user_repository.list_by_company(principal.company_id)
        return [
            AuthPrincipal(
                user_id=user.user_id,
                email=user.email,
                company_id=principal.company_id,
                roles=tuple(user.roles_for_company(principal.company_id)),
            )
            for user in users
        ]


class AuthorizeRolesUseCase:
    def execute(self, principal: AuthPrincipal, allowed_roles: set[str]) -> None:
        if not set(principal.roles).intersection(allowed_roles):
            raise RoleAccessDeniedError("insufficient role")
