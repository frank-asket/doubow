import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.users_service import ensure_user


@pytest.mark.asyncio
async def test_ensure_user_returns_existing_when_fallback_commit_fails(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: second commit failure inside IntegrityError fallback should not escape uncaught."""
    user = User(id="user_fallback_commit", email="original@example.com", name="Original", plan="free")
    db_session.add(user)
    db_session.add(User(id="user_conflict", email="dupe@example.com", name="Conflict", plan="free"))
    await db_session.commit()

    original_commit = db_session.commit
    commit_calls = 0

    async def commit_with_second_failure() -> None:
        nonlocal commit_calls
        commit_calls += 1
        if commit_calls == 2:
            raise SQLAlchemyError("forced second commit failure")
        await original_commit()

    monkeypatch.setattr(db_session, "commit", commit_with_second_failure)

    claims = {"email": "dupe@example.com", "name": "Updated Name", "public_metadata": {"plan": "pro"}}
    recovered = await ensure_user(db_session, user.id, claims)

    assert recovered.id == user.id
    assert commit_calls == 2
