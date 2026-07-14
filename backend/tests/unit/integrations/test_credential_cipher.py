from app.modules.integrations.infrastructure.security import CredentialCipher


def test_credential_cipher_encrypts_and_decrypts() -> None:
    cipher = CredentialCipher(key_seed="unit-test-key")
    credentials = {
        "app_key": "abc",
        "app_secret": "secret-123",
        "nested": {"token": "top-secret"},
    }

    encrypted = cipher.encrypt(credentials)
    assert encrypted != ""
    assert "secret-123" not in encrypted

    restored = cipher.decrypt(encrypted)
    assert restored["app_key"] == "abc"
    assert restored["app_secret"] == "secret-123"

    masked = cipher.mask(credentials)
    assert masked["app_secret"] == "***"
    assert masked["nested"]["token"] == "***"
