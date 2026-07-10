from passlib.context import CryptContext

from app.modules.auth.application.ports.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def hash(self, plain_password: str) -> str:
        return self._context.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return self._context.verify(plain_password, password_hash)
