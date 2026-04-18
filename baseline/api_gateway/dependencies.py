from functools import lru_cache

import jwt
from fastapi import Header, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient

from config import settings


@lru_cache(maxsize=4)
def _jwks_client_for_issuer(issuer: str) -> PyJWKClient:
    return PyJWKClient(f"{issuer.rstrip('/')}/.well-known/jwks.json")


def _decode_clerk_token(token: str) -> dict:
    unverified = jwt.decode(token, options={"verify_signature": False})
    issuer = unverified.get("iss")
    if not isinstance(issuer, str) or not issuer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

    if settings.clerk_issuer and issuer.rstrip("/") != settings.clerk_issuer.rstrip("/"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token issuer mismatch")

    jwks_client = _jwks_client_for_issuer(issuer)
    signing_key = jwks_client.get_signing_key_from_jwt(token).key

    options = {"verify_aud": bool(settings.clerk_audience)}
    decode_kwargs: dict[str, str | list[str] | bool] = {"issuer": issuer, "algorithms": ["RS256"], "options": options}
    if settings.clerk_audience:
        decode_kwargs["audience"] = settings.clerk_audience

    return jwt.decode(token, signing_key, **decode_kwargs)


def get_current_user_id(authorization: str | None = Header(default=None, alias="Authorization")) -> str:
    claims = get_current_user_claims(authorization=authorization)
    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    return user_id


def get_current_user_claims(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization scheme")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        claims = _decode_clerk_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token") from exc

    return claims


def require_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required Idempotency-Key header",
        )
    if len(idempotency_key.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key must be at least 8 characters",
        )
    return idempotency_key.strip()
