from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.modules.auth.application.schemas import AuthenticateCommand, LogoutCommand, RefreshCommand
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.domain.errors import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    TenantAccessDeniedError,
    TokenRevokedError,
)
from app.modules.auth.infrastructure.container import AuthContainer
from app.modules.auth.interfaces.api.dependencies import get_auth_container, get_current_principal, require_roles
from app.modules.auth.interfaces.api.schemas import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    container: AuthContainer = Depends(get_auth_container),
) -> TokenResponse:
    try:
        result = container.authenticate_user.execute(
            AuthenticateCommand(
                email=payload.email,
                password=payload.password,
                company_id=payload.company_id,
                correlation_id=request.headers.get("X-Correlation-ID"),
            )
        )
    except (InvalidCredentialsError, InactiveUserError, TenantAccessDeniedError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
        refresh_expires_in=result.refresh_expires_in,
    )


@router.post("/refresh")
def refresh(
    payload: RefreshRequest,
    request: Request,
    container: AuthContainer = Depends(get_auth_container),
) -> TokenResponse:
    try:
        result = container.refresh_session.execute(
            RefreshCommand(
                refresh_token=payload.refresh_token,
                correlation_id=request.headers.get("X-Correlation-ID"),
            )
        )
    except (InvalidTokenError, TokenRevokedError, TenantAccessDeniedError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
        refresh_expires_in=result.refresh_expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    request: Request,
    container: AuthContainer = Depends(get_auth_container),
) -> None:
    try:
        container.logout.execute(
            LogoutCommand(
                refresh_token=payload.refresh_token,
                correlation_id=request.headers.get("X-Correlation-ID"),
            )
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me")
def me(principal: AuthPrincipal = Depends(get_current_principal)) -> MeResponse:
    return MeResponse(
        user_id=principal.user_id,
        email=principal.email,
        company_id=principal.company_id,
        roles=list(principal.roles),
    )


@router.get("/users")
def list_company_users(
    principal: AuthPrincipal = Depends(require_roles("owner", "admin")),
    container: AuthContainer = Depends(get_auth_container),
) -> list[UserResponse]:
    users = container.list_company_users.execute(principal)
    return [
        UserResponse(
            user_id=user.user_id,
            email=user.email,
            company_id=user.company_id,
            roles=list(user.roles),
        )
        for user in users
    ]
