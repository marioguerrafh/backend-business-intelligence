from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet

from app.config.settings import settings


@dataclass(slots=True)
class CredentialCipher:
    key_seed: str

    @classmethod
    def from_settings(cls) -> "CredentialCipher":
        return cls(key_seed=settings.jwt_secret_key)

    def _fernet(self) -> Fernet:
        digest = hashlib.sha256(self.key_seed.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def encrypt(self, credentials: dict[str, Any]) -> str:
        payload = json.dumps(credentials, separators=(",", ":")).encode("utf-8")
        token = self._fernet().encrypt(payload)
        return token.decode("utf-8")

    def decrypt(self, encrypted_credentials: str) -> dict[str, Any]:
        raw = self._fernet().decrypt(encrypted_credentials.encode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict):
            return data
        raise ValueError("invalid encrypted credentials payload")

    def mask(self, credentials: dict[str, Any]) -> dict[str, Any]:
        masked: dict[str, Any] = {}
        for key, value in credentials.items():
            lower = key.lower()
            if lower in {"app_secret", "token", "password", "secret", "api_key", "client_secret"}:
                masked[key] = "***"
                continue
            if isinstance(value, dict):
                masked[key] = self.mask(value)
                continue
            masked[key] = value
        return masked
