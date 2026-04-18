from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.users import MeResponse


def _extract_email(claims: dict, user_id: str) -> str:
    email = claims.get("email")
    if isinstance(email, str) and email:
        return email
    email_addresses = claims.get("email_addresses")
    if isinstance(email_addresses, list) and email_addresses:
        first = email_addresses[0]
        if isinstance(first, dict):
            nested = first.get("email_address")
            if isinstance(nested, str) and nested:
                return nested
    return f"{user_id}@clerk.local"


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
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    email = _extract_email(claims, user_id)
    name = _extract_name(claims)
    plan = _extract_plan(claims)

    if user is None:
        user = User(id=user_id, email=email, name=name, plan=plan)
        session.add(user)
    else:
        # Keep user profile synchronized with Clerk claims.
        user.email = email
        user.name = name
        user.plan = plan

    await session.commit()
    await session.refresh(user)

    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name or "Doubow User",
        plan="pro" if user.plan == "pro" else "free",
    )
