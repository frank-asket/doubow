from fastapi import Header, HTTPException, status


def get_current_user_id() -> str:
    # TODO: replace with real auth context from Supabase/NextAuth session.
    return "dev-user"


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
