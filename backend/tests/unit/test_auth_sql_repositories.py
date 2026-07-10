from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.modules.auth.domain.entities import CompanyMembership, RefreshSession, Role, UserAccount
from app.modules.auth.infrastructure.models import AuthRefreshSessionModel, AuthUserMembershipModel, AuthUserModel
from app.modules.auth.infrastructure.repositories import (
    SqlAlchemyRefreshSessionRepository,
    SqlAlchemyUserRepository,
)
from app.shared.infrastructure.db.base import Base


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AuthUserModel.__table__,
            AuthUserMembershipModel.__table__,
            AuthRefreshSessionModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_sqlalchemy_user_repository_roundtrip() -> None:
    session = _session()
    repository = SqlAlchemyUserRepository(session)

    user = UserAccount(
        user_id="u_sql_1",
        email="owner@acme.com",
        password_hash="hash",
        is_active=True,
        memberships=(
            CompanyMembership(company_id="cmp_acme", roles=frozenset({Role.OWNER, Role.ADMIN})),
            CompanyMembership(company_id="cmp_omega", roles=frozenset({Role.VIEWER})),
        ),
    )

    repository.upsert(user)
    session.commit()

    by_email = repository.get_by_email("owner@acme.com")
    assert by_email is not None
    assert by_email.belongs_to_company("cmp_acme")
    assert set(by_email.roles_for_company("cmp_acme")) == {"owner", "admin"}

    company_users = repository.list_by_company("cmp_omega")
    assert len(company_users) == 1
    assert company_users[0].user_id == "u_sql_1"


def test_sqlalchemy_refresh_repository_roundtrip() -> None:
    session = _session()
    repository = SqlAlchemyRefreshSessionRepository(session)

    refresh = RefreshSession(
        token_id="t_sql_1",
        user_id="u_sql_1",
        company_id="cmp_acme",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    repository.save(refresh)
    session.commit()

    stored = repository.get("t_sql_1")
    assert stored is not None
    assert stored.user_id == "u_sql_1"

    repository.revoke("t_sql_1", replaced_by="t_sql_2")
    session.commit()

    revoked = repository.get("t_sql_1")
    assert revoked is not None
    assert revoked.revoked_at is not None
    assert revoked.replaced_by_token_id == "t_sql_2"
