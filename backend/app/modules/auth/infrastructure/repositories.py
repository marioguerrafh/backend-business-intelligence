from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.application.ports.refresh_session_repository import RefreshSessionRepository
from app.modules.auth.application.ports.user_repository import UserRepository
from app.modules.auth.domain.entities import CompanyMembership, RefreshSession, Role, UserAccount
from app.modules.auth.infrastructure.models import AuthRefreshSessionModel, AuthUserMembershipModel, AuthUserModel


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[UserAccount] | None = None) -> None:
        self._by_id: dict[str, UserAccount] = {}
        self._by_email: dict[str, UserAccount] = {}
        if users:
            for user in users:
                self._by_id[user.user_id] = user
                self._by_email[user.email.lower()] = user

    def get_by_email(self, email: str) -> UserAccount | None:
        return self._by_email.get(email.lower())

    def get_by_id(self, user_id: str) -> UserAccount | None:
        return self._by_id.get(user_id)

    def list_by_company(self, company_id: str) -> list[UserAccount]:
        return [user for user in self._by_id.values() if user.belongs_to_company(company_id)]


class InMemoryRefreshSessionRepository(RefreshSessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[str, RefreshSession] = {}

    def save(self, session: RefreshSession) -> None:
        self._sessions[session.token_id] = session

    def get(self, token_id: str) -> RefreshSession | None:
        return self._sessions.get(token_id)

    def revoke(self, token_id: str, replaced_by: str | None = None) -> None:
        session = self._sessions.get(token_id)
        if session is None:
            return
        session.revoked_at = datetime.now(timezone.utc)
        session.replaced_by_token_id = replaced_by


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserAccount | None:
        stmt = select(AuthUserModel).where(AuthUserModel.email == email.lower())
        user_model = self.session.execute(stmt).scalar_one_or_none()
        if user_model is None:
            return None
        return self._to_entity(user_model)

    def get_by_id(self, user_id: str) -> UserAccount | None:
        user_model = self.session.get(AuthUserModel, user_id)
        if user_model is None:
            return None
        return self._to_entity(user_model)

    def list_by_company(self, company_id: str) -> list[UserAccount]:
        stmt = (
            select(AuthUserModel)
            .join(AuthUserMembershipModel, AuthUserMembershipModel.user_id == AuthUserModel.id)
            .where(AuthUserMembershipModel.company_id == company_id)
        )
        models = self.session.execute(stmt).scalars().unique().all()
        return [self._to_entity(model) for model in models]

    def upsert(self, user: UserAccount) -> None:
        model = self.session.get(AuthUserModel, user.user_id)
        if model is None:
            model = AuthUserModel(
                id=user.user_id,
                email=user.email.lower(),
                password_hash=user.password_hash,
                is_active=user.is_active,
            )
            self.session.add(model)
        else:
            model.email = user.email.lower()
            model.password_hash = user.password_hash
            model.is_active = user.is_active

        model.memberships = []
        for membership in user.memberships:
            for role in membership.roles:
                model.memberships.append(
                    AuthUserMembershipModel(
                        id=str(uuid4()),
                        user_id=user.user_id,
                        company_id=membership.company_id,
                        role=role.value,
                    )
                )

    def _to_entity(self, model: AuthUserModel) -> UserAccount:
        by_company: dict[str, set[Role]] = {}
        for membership in model.memberships:
            by_company.setdefault(membership.company_id, set()).add(Role(membership.role))

        memberships = tuple(
            CompanyMembership(company_id=company_id, roles=frozenset(roles))
            for company_id, roles in by_company.items()
        )
        return UserAccount(
            user_id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            is_active=model.is_active,
            memberships=memberships,
        )


class SqlAlchemyRefreshSessionRepository(RefreshSessionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, session: RefreshSession) -> None:
        model = self.session.get(AuthRefreshSessionModel, session.token_id)
        if model is None:
            model = AuthRefreshSessionModel(
                token_id=session.token_id,
                user_id=session.user_id,
                company_id=session.company_id,
                issued_at=session.issued_at,
                expires_at=session.expires_at,
                revoked_at=session.revoked_at,
                replaced_by_token_id=session.replaced_by_token_id,
            )
            self.session.add(model)
            return

        model.user_id = session.user_id
        model.company_id = session.company_id
        model.issued_at = session.issued_at
        model.expires_at = session.expires_at
        model.revoked_at = session.revoked_at
        model.replaced_by_token_id = session.replaced_by_token_id

    def get(self, token_id: str) -> RefreshSession | None:
        model = self.session.get(AuthRefreshSessionModel, token_id)
        if model is None:
            return None
        return RefreshSession(
            token_id=model.token_id,
            user_id=model.user_id,
            company_id=model.company_id,
            issued_at=model.issued_at,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by_token_id=model.replaced_by_token_id,
        )

    def revoke(self, token_id: str, replaced_by: str | None = None) -> None:
        model = self.session.get(AuthRefreshSessionModel, token_id)
        if model is None:
            return
        model.revoked_at = datetime.now(timezone.utc)
        model.replaced_by_token_id = replaced_by


def build_seed_users(admin_hash: str, analyst_hash: str) -> list[UserAccount]:
    return [
        UserAccount(
            user_id="usr_owner_001",
            email="owner@acme.com",
            password_hash=admin_hash,
            is_active=True,
            memberships=(
                CompanyMembership(company_id="cmp_acme", roles=frozenset({Role.OWNER, Role.ADMIN})),
                CompanyMembership(company_id="cmp_omega", roles=frozenset({Role.VIEWER})),
            ),
        ),
        UserAccount(
            user_id="usr_analyst_001",
            email="analyst@acme.com",
            password_hash=analyst_hash,
            is_active=True,
            memberships=(
                CompanyMembership(company_id="cmp_acme", roles=frozenset({Role.ANALYST})),
            ),
        ),
    ]


def seed_users_if_empty(session: Session, admin_hash: str, analyst_hash: str) -> None:
    has_users = session.execute(select(AuthUserModel.id).limit(1)).scalar_one_or_none() is not None
    if has_users:
        return

    repository = SqlAlchemyUserRepository(session)
    for user in build_seed_users(admin_hash, analyst_hash):
        repository.upsert(user)
