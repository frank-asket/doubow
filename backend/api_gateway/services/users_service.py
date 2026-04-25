from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.users import MeResponse


def normalize_clerk_subject(sub: str) -> str:
    """Stable primary key for users.id from Clerk JWT `sub` (trimmed, non-empty)."""
    normalized = sub.strip()
    if not normalized:
        raise ValueError("empty Clerk subject")
    if len(normalized) > 128:
        raise ValueError("Clerk subject too long")
    return normalized


async def ensure_user(session: AsyncSession, user_id: str, claims: dict) -> User:
    """Upsert the users row from Clerk claims and persist. Call on every authenticated request."""
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    email = _extract_email(claims, user_id)
    name = _extract_name(claims)
    plan = _extract_plan(claims)

    if user is None:
        user = User(id=user_id, email=email, name=name, plan=plan)
        session.add(user)
    else:
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if user.name != name:
            user.name = name
            changed = True
        if user.plan != plan:
            user.plan = plan
            changed = True
        if not changed:
            return user

    try:
        await session.commit()
    except (IntegrityError, DataError):
        # Most common in production: unique(email) collision across Clerk subjects.
        # Keep auth path resilient by falling back to a deterministic local email.
        await session.rollback()
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        fallback_email = _fallback_email_for_user(user_id)
        if user is None:
            user = User(id=user_id, email=fallback_email, name=name, plan=plan)
            session.add(user)
        else:
            user.email = fallback_email
            user.name = name
            user.plan = plan
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        # For auth path stability, return existing row when available rather than hard-failing all routes.
        existing = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if existing is not None:
            return existing
        raise
    await session.refresh(user)
    return user


def user_to_me_response(user: User) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name or "Doubow User",
        plan="pro" if user.plan == "pro" else "free",
    )


def _extract_email(claims: dict, user_id: str) -> str:
    email = claims.get("email")
    if isinstance(email, str) and email:
        return _normalize_email(email, user_id)
    email_addresses = claims.get("email_addresses")
    if isinstance(email_addresses, list) and email_addresses:
        first = email_addresses[0]
        if isinstance(first, dict):
            nested = first.get("email_address")
            if isinstance(nested, str) and nested:
                return _normalize_email(nested, user_id)
    return _fallback_email_for_user(user_id)


def _fallback_email_for_user(user_id: str) -> str:
    token = "".join(ch for ch in user_id.lower() if ch.isalnum())[:40] or "user"
    return f"{token}@clerk.local"


def _normalize_email(email: str, user_id: str) -> str:
    normalized = email.strip().lower()
    if normalized and len(normalized) <= 255:
        return normalized
    return _fallback_email_for_user(user_id)


def _extract_name(claims: dict) -> str | None:
    full_name = claims.get("name")
    if isinstance(full_name, str) and full_name.strip():
        return full_name.strip()
    first = claims.get("given_name")
    last = claims.get("family_name")
    if isinstance(first, str) and isinstance(last, str):
        combined = f"{first} {last}".strip()
        return combined or None
    return None


def _extract_plan(claims: dict) -> str:
    public_metadata = claims.get("public_metadata")
    if not isinstance(public_metadata, dict):
        return "free"
    status = public_metadata.get("subscriptionStatus")
    if status == "active":
        return "pro"
    plan = public_metadata.get("plan")
    if isinstance(plan, str) and plan.lower() == "pro":
        return "pro"
    return "free"


async def get_me(session: AsyncSession, user_id: str, claims: dict) -> MeResponse:
    user = await ensure_user(session, user_id, claims)
    return user_to_me_response(user)
