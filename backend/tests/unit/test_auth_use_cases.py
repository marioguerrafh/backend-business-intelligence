from datetime import datetime, timedelta, timezone

import pytest

from app.modules.auth.application.schemas import AuthenticateCommand, RefreshCommand
from app.modules.auth.application.use_cases import AuthenticateUserUseCase, RefreshSessionUseCase
from app.modules.auth.domain.entities import CompanyMembership, RefreshSession, Role, UserAccount
from app.modules.auth.domain.errors import InvalidCredentialsError, TokenRevokedError
from app.modules.auth.infrastructure.clock import SystemClock
from app.modules.auth.infrastructure.jwt_service import JwtTokenService
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.modules.auth.infrastructure.repositories import (
    InMemoryRefreshSessionRepository,
    InMemoryUserRepository,
)


def _build_user(hasher: BcryptPasswordHasher) -> UserAccount:
    return UserAccount(
        user_id="u1",
        email="owner@acme.com",
        password_hash=hasher.hash("Owner@123"),
        is_active=True,
        memberships=(
            CompanyMembership(company_id="cmp_acme", roles=frozenset({Role.OWNER, Role.ADMIN})),
        ),
    )


def test_authenticate_user_success() -> None:
    hasher = BcryptPasswordHasher()
    user_repo = InMemoryUserRepository([_build_user(hasher)])
    refresh_repo = InMemoryRefreshSessionRepository()
    token_service = JwtTokenService()

    use_case = AuthenticateUserUseCase(
        user_repository=user_repo,
        password_hasher=hasher,
        token_service=token_service,
        refresh_repository=refresh_repo,
        logger=__import__("logging").getLogger("test.auth"),
    )

    tokens = use_case.execute(
        AuthenticateCommand(email="owner@acme.com", password="Owner@123", company_id="cmp_acme")
    )

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


def test_authenticate_user_invalid_password() -> None:
    hasher = BcryptPasswordHasher()
    user_repo = InMemoryUserRepository([_build_user(hasher)])
    refresh_repo = InMemoryRefreshSessionRepository()
    token_service = JwtTokenService()

    use_case = AuthenticateUserUseCase(
        user_repository=user_repo,
        password_hasher=hasher,
        token_service=token_service,
        refresh_repository=refresh_repo,
        logger=__import__("logging").getLogger("test.auth"),
    )

    with pytest.raises(InvalidCredentialsError):
        use_case.execute(
            AuthenticateCommand(email="owner@acme.com", password="wrong-pass", company_id="cmp_acme")
        )


def test_refresh_rotation_revokes_old_session() -> None:
    hasher = BcryptPasswordHasher()
    user = _build_user(hasher)
    user_repo = InMemoryUserRepository([user])
    refresh_repo = InMemoryRefreshSessionRepository()
    token_service = JwtTokenService()

    auth_use_case = AuthenticateUserUseCase(
        user_repository=user_repo,
        password_hasher=hasher,
        token_service=token_service,
        refresh_repository=refresh_repo,
        logger=__import__("logging").getLogger("test.auth"),
    )
    refresh_use_case = RefreshSessionUseCase(
        user_repository=user_repo,
        token_service=token_service,
        refresh_repository=refresh_repo,
        clock=SystemClock(),
        logger=__import__("logging").getLogger("test.auth"),
    )

    initial = auth_use_case.execute(
        AuthenticateCommand(email="owner@acme.com", password="Owner@123", company_id="cmp_acme")
    )
    rotated = refresh_use_case.execute(RefreshCommand(refresh_token=initial.refresh_token))

    assert rotated.refresh_token != initial.refresh_token

    with pytest.raises(TokenRevokedError):
        refresh_use_case.execute(RefreshCommand(refresh_token=initial.refresh_token))


def test_refresh_rejects_expired_session() -> None:
    hasher = BcryptPasswordHasher()
    user = _build_user(hasher)
    user_repo = InMemoryUserRepository([user])
    refresh_repo = InMemoryRefreshSessionRepository()
    token_service = JwtTokenService()

    pair, session = token_service.issue_token_pair(
        subject=user.user_id,
        email=user.email,
        company_id="cmp_acme",
        roles=["owner"],
    )
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    refresh_repo.save(session)

    refresh_use_case = RefreshSessionUseCase(
        user_repository=user_repo,
        token_service=token_service,
        refresh_repository=refresh_repo,
        clock=SystemClock(),
        logger=__import__("logging").getLogger("test.auth"),
    )

    with pytest.raises(TokenRevokedError):
        refresh_use_case.execute(RefreshCommand(refresh_token=pair.refresh_token))
