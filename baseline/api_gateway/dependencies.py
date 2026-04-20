from collections.abc import AsyncGenerator
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import bind_request_user_for_rls, get_session, reset_request_user_rls
from models.user import User
from services.users_service import ensure_user, normalize_clerk_subject


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
    try:
        return normalize_clerk_subject(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc


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


async def get_authenticated_user(
    claims: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[User, None]:
    raw_sub = claims.get("sub")
    if not isinstance(raw_sub, str) or not raw_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    try:
        user_id = normalize_clerk_subject(raw_sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc

    token = bind_request_user_for_rls(user_id)
    try:
        user = await ensure_user(session, user_id, claims)
        yield user
    finally:
        reset_request_user_rls(token)


def optional_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str | None:
    """Same validation as required idempotency when the header is present; omitted/blank means no replay semantics."""
    if idempotency_key is None:
        return None
    stripped = idempotency_key.strip()
    if not stripped:
        return None
    if len(stripped) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key must be at least 8 characters",
        )
    return stripped


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
