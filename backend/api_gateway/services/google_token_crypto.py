"""Encrypt/decrypt Google refresh tokens at rest."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from config import settings


class GoogleTokenCryptoError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = settings.google_oauth_token_fernet_key
    if not key:
        raise GoogleTokenCryptoError("GOOGLE_OAUTH_TOKEN_FERNET_KEY is not set")
    raw = key.strip().encode("utf-8")
    return Fernet(raw)


def encrypt_refresh_token(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_refresh_token(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise GoogleTokenCryptoError("failed to decrypt stored token") from exc
