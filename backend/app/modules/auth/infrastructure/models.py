from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.db.base import Base


class AuthUserModel(Base):
    __tablename__ = "auth_users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    memberships: Mapped[list["AuthUserMembershipModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AuthUserMembershipModel(Base):
    __tablename__ = "auth_user_memberships"
    __table_args__ = (UniqueConstraint("user_id", "company_id", "role", name="uq_auth_membership_role"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("auth_users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)

    user: Mapped[AuthUserModel] = relationship(back_populates="memberships")


class AuthRefreshSessionModel(Base):
    __tablename__ = "auth_refresh_sessions"

    token_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_token_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
