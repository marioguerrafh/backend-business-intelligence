from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.config.settings import settings
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.domain.errors import InvalidTokenError, RoleAccessDeniedError
from app.modules.auth.infrastructure.container import (
    AuthContainer,
    build_in_memory_auth_container,
    build_sql_auth_container,
)

_memory_container = build_in_memory_auth_container()
_bearer = HTTPBearer(auto_error=False)


def get_auth_container(db: Session = Depends(get_db)):
    if settings.auth_storage_mode.lower() != "sql":
        yield _memory_container
        return

    container = build_sql_auth_container(session=db)
    try:
        yield container
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: AuthContainer = Depends(get_auth_container),
) -> AuthPrincipal:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    try:
        return container.get_current_principal.execute(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_roles(*roles: str) -> Callable[[AuthPrincipal, AuthContainer], AuthPrincipal]:
    allowed = {role.lower() for role in roles}

    def _dependency(
        principal: AuthPrincipal = Depends(get_current_principal),
        container: AuthContainer = Depends(get_auth_container),
    ) -> AuthPrincipal:
        try:
            container.authorize_roles.execute(principal=principal, allowed_roles=allowed)
            return principal
        except RoleAccessDeniedError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return _dependency
