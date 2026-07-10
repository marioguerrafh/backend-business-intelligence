from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from app.config.settings import settings
from app.modules.auth.application.ports.token_service import TokenClaims, TokenService
from app.modules.auth.domain.entities import RefreshSession, TokenPair
from app.modules.auth.domain.errors import InvalidTokenError


class JwtTokenService(TokenService):
    def __init__(self) -> None:
        self.secret = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.issuer = settings.jwt_issuer
        self.audience = settings.jwt_audience
        self.access_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_minutes = settings.jwt_refresh_token_expire_minutes

    def issue_token_pair(self, subject: str, email: str, company_id: str, roles: list[str]) -> tuple[TokenPair, RefreshSession]:
        issued_at = datetime.now(timezone.utc)
        access_token_id = str(uuid4())
        refresh_token_id = str(uuid4())

        access_exp = issued_at + timedelta(minutes=self.access_minutes)
        refresh_exp = issued_at + timedelta(minutes=self.refresh_minutes)

        access_payload = self._base_payload(
            token_id=access_token_id,
            token_type="access",
            subject=subject,
            email=email,
            company_id=company_id,
            roles=roles,
            issued_at=issued_at,
            expires_at=access_exp,
        )
        refresh_payload = self._base_payload(
            token_id=refresh_token_id,
            token_type="refresh",
            subject=subject,
            email=email,
            company_id=company_id,
            roles=roles,
            issued_at=issued_at,
            expires_at=refresh_exp,
        )

        access_token = jwt.encode(access_payload, self.secret, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret, algorithm=self.algorithm)
        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_minutes * 60,
            refresh_expires_in=self.refresh_minutes * 60,
        )
        refresh_session = RefreshSession(
            token_id=refresh_token_id,
            user_id=subject,
            company_id=company_id,
            issued_at=issued_at,
            expires_at=refresh_exp,
        )
        return token_pair, refresh_session

    def decode_access_token(self, token: str) -> TokenClaims:
        return self._decode(token=token, expected_type="access")

    def decode_refresh_token(self, token: str) -> TokenClaims:
        return self._decode(token=token, expected_type="refresh")

    def _decode(self, token: str, expected_type: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={"require_sub": True, "require_exp": True, "require_iat": True},
            )
        except JWTError as exc:
            raise InvalidTokenError("invalid token") from exc

        token_type = str(payload.get("typ", ""))
        if token_type != expected_type:
            raise InvalidTokenError("invalid token type")

        roles_raw = payload.get("roles") or []
        if not isinstance(roles_raw, list):
            raise InvalidTokenError("invalid roles claim")

        try:
            return TokenClaims(
                token_id=str(payload["jti"]),
                token_type=token_type,
                subject=str(payload["sub"]),
                company_id=str(payload["company_id"]),
                roles=tuple(str(role) for role in roles_raw),
                issued_at=datetime.fromtimestamp(int(payload["iat"]), timezone.utc),
                expires_at=datetime.fromtimestamp(int(payload["exp"]), timezone.utc),
                email=str(payload.get("email", "")),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidTokenError("malformed token payload") from exc

    def _base_payload(
        self,
        token_id: str,
        token_type: str,
        subject: str,
        email: str,
        company_id: str,
        roles: list[str],
        issued_at: datetime,
        expires_at: datetime,
    ) -> dict[str, object]:
        iat = int(issued_at.timestamp())
        exp = int(expires_at.timestamp())
        return {
            "jti": token_id,
            "typ": token_type,
            "sub": subject,
            "email": email,
            "company_id": company_id,
            "roles": roles,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": iat,
            "nbf": iat,
            "exp": exp,
        }
