"""Encrypt/decrypt LinkedIn OAuth tokens at rest."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from config import settings


class LinkedInTokenCryptoError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = settings.linkedin_oauth_token_fernet_key or settings.google_oauth_token_fernet_key
    if not key:
        raise LinkedInTokenCryptoError(
            "LINKEDIN_OAUTH_TOKEN_FERNET_KEY (or GOOGLE_OAUTH_TOKEN_FERNET_KEY fallback) is not set"
        )
    raw = key.strip().encode("utf-8")
    return Fernet(raw)


def encrypt_access_token(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_access_token(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise LinkedInTokenCryptoError("failed to decrypt stored token") from exc

