import pytest

from models.user import User
from services.agent_chat_service import (
    append_chat_message,
    ensure_thread_for_user,
    get_chat_thread_for_user,
    list_chat_threads_for_user,
)


@pytest.mark.asyncio
async def test_chat_thread_create_append_and_fetch(db_session):
    user_id = "user_chat_1"
    db_session.add(User(id=user_id, email="chat1@example.com"))
    await db_session.commit()

    thread = await ensure_thread_for_user(db_session, user_id=user_id, thread_id=None)
    await append_chat_message(db_session, thread=thread, role="user", content="Hello")
    await append_chat_message(db_session, thread=thread, role="assistant", content="Hi there")
    await db_session.commit()

    listed, has_more = await list_chat_threads_for_user(db_session, user_id=user_id, limit=10)
    assert len(listed) == 1
    assert listed[0].id == thread.id
    assert has_more is False

    detail = await get_chat_thread_for_user(db_session, user_id=user_id, thread_id=thread.id)
    assert detail is not None
    assert [m.role for m in detail.messages] == ["user", "assistant"]
    assert [m.content for m in detail.messages] == ["Hello", "Hi there"]


@pytest.mark.asyncio
async def test_chat_thread_is_user_scoped(db_session):
    db_session.add_all(
        [
            User(id="user_chat_owner", email="owner@example.com"),
            User(id="user_chat_other", email="other@example.com"),
        ]
    )
    await db_session.commit()

    thread = await ensure_thread_for_user(db_session, user_id="user_chat_owner", thread_id=None)
    await append_chat_message(db_session, thread=thread, role="user", content="owner note")
    await db_session.commit()

    denied = await get_chat_thread_for_user(db_session, user_id="user_chat_other", thread_id=thread.id)
    assert denied is None
