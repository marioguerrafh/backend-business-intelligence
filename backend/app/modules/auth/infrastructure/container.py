import logging
from dataclasses import dataclass
from typing import cast

from sqlalchemy import Table
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.modules.auth.application.use_cases import (
    AuthenticateUserUseCase,
    AuthorizeRolesUseCase,
    GetCurrentPrincipalUseCase,
    ListCompanyUsersUseCase,
    LogoutUseCase,
    RefreshSessionUseCase,
)
from app.modules.auth.infrastructure.clock import SystemClock
from app.modules.auth.infrastructure.jwt_service import JwtTokenService
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.modules.auth.infrastructure.models import AuthRefreshSessionModel, AuthUserMembershipModel, AuthUserModel
from app.modules.auth.infrastructure.repositories import (
    InMemoryRefreshSessionRepository,
    InMemoryUserRepository,
    SqlAlchemyRefreshSessionRepository,
    SqlAlchemyUserRepository,
    build_seed_users,
    seed_users_if_empty,
)
from app.shared.infrastructure.db.base import Base


@dataclass(slots=True)
class AuthContainer:
    authenticate_user: AuthenticateUserUseCase
    refresh_session: RefreshSessionUseCase
    logout: LogoutUseCase
    get_current_principal: GetCurrentPrincipalUseCase
    authorize_roles: AuthorizeRolesUseCase
    list_company_users: ListCompanyUsersUseCase


def _build_auth_container(user_repository, refresh_repository) -> AuthContainer:
    logger = logging.getLogger("app.auth")
    password_hasher = BcryptPasswordHasher()
    token_service = JwtTokenService()
    clock = SystemClock()

    return AuthContainer(
        authenticate_user=AuthenticateUserUseCase(
            user_repository=user_repository,
            password_hasher=password_hasher,
            token_service=token_service,
            refresh_repository=refresh_repository,
            logger=logger,
        ),
        refresh_session=RefreshSessionUseCase(
            user_repository=user_repository,
            token_service=token_service,
            refresh_repository=refresh_repository,
            clock=clock,
            logger=logger,
        ),
        logout=LogoutUseCase(token_service=token_service, refresh_repository=refresh_repository),
        get_current_principal=GetCurrentPrincipalUseCase(token_service=token_service),
        authorize_roles=AuthorizeRolesUseCase(),
        list_company_users=ListCompanyUsersUseCase(user_repository=user_repository),
    )


def build_in_memory_auth_container() -> AuthContainer:
    password_hasher = BcryptPasswordHasher()
    users = build_seed_users(
        admin_hash=password_hasher.hash("Owner@123"),
        analyst_hash=password_hasher.hash("Analyst@123"),
    )
    user_repository = InMemoryUserRepository(users=users)
    refresh_repository = InMemoryRefreshSessionRepository()
    return _build_auth_container(user_repository=user_repository, refresh_repository=refresh_repository)


def build_sql_auth_container(session: Session) -> AuthContainer:
    bind = session.get_bind()
    Base.metadata.create_all(
        bind=bind,
        tables=(
            cast(Table, AuthUserModel.__table__),
            cast(Table, AuthUserMembershipModel.__table__),
            cast(Table, AuthRefreshSessionModel.__table__),
        ),
    )

    user_repository = SqlAlchemyUserRepository(session=session)
    refresh_repository = SqlAlchemyRefreshSessionRepository(session=session)

    if settings.auth_seed_demo_users:
        password_hasher = BcryptPasswordHasher()
        seed_users_if_empty(
            session=session,
            admin_hash=password_hasher.hash("Owner@123"),
            analyst_hash=password_hasher.hash("Analyst@123"),
        )
        session.commit()

    return _build_auth_container(user_repository=user_repository, refresh_repository=refresh_repository)
