import pytest

from models.user import User
from services.profile_views_service import increment_profile_views


@pytest.mark.asyncio
async def test_increment_profile_views_from_null(db_session):
    uid = "user_pv_inc"
    db_session.add(User(id=uid, email="pvinc@example.com", profile_views=None))
    await db_session.commit()

    total = await increment_profile_views(db_session, uid, delta=1)
    assert total == 1

    row = await db_session.get(User, uid)
    assert row is not None
    assert row.profile_views == 1


@pytest.mark.asyncio
async def test_increment_profile_views_accumulates(db_session):
    uid = "user_pv_acc"
    db_session.add(User(id=uid, email="pvacc@example.com", profile_views=10))
    await db_session.commit()

    total = await increment_profile_views(db_session, uid, delta=3)
    assert total == 13


@pytest.mark.asyncio
async def test_increment_profile_views_unknown_user_raises(db_session):
    with pytest.raises(LookupError, match="user not found"):
        await increment_profile_views(db_session, "does_not_exist", delta=1)
