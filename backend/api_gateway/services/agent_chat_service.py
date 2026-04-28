from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat_message import ChatMessage
from models.chat_thread import ChatThread
from schemas.agents import (
    ChatMessageResponse,
    ChatThreadDetailResponse,
    ChatThreadSummaryResponse,
)


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return datetime.now(timezone.utc).isoformat()
    return dt.isoformat()


def _to_summary(row: ChatThread) -> ChatThreadSummaryResponse:
    title = (row.title or "").strip() or "Conversation"
    return ChatThreadSummaryResponse(
        id=row.id,
        title=title,
        updated_at=_iso(row.updated_at),
        created_at=_iso(row.created_at),
    )


async def ensure_thread_for_user(
    session: AsyncSession,
    *,
    user_id: str,
    thread_id: str | None,
) -> ChatThread:
    if thread_id:
        row = await session.get(ChatThread, thread_id)
        if row is not None and row.user_id == user_id:
            return row
    row = ChatThread(user_id=user_id, title=None)
    session.add(row)
    await session.flush()
    return row


async def append_chat_message(
    session: AsyncSession,
    *,
    thread: ChatThread,
    role: str,
    content: str,
) -> None:
    body = content.strip()
    if not body:
        return
    # Set created_at in the app so ordering is stable (server_default can tie on SQLite/CI).
    msg = ChatMessage(
        thread_id=thread.id,
        role=role,
        content=body,
        created_at=datetime.now(timezone.utc),
    )
    session.add(msg)
    # Touch updated_at even on DBs without ON UPDATE trigger semantics.
    thread.updated_at = datetime.now(timezone.utc)
    if role == "user" and not (thread.title or "").strip():
        thread.title = body[:120]
    await session.flush()


def _trim_transcript_by_chars(chronological: list[ChatMessage], max_chars: int) -> list[ChatMessage]:
    """Drop oldest turns until the transcript fits ``max_chars`` (keeps latest user/assistant tail)."""
    if max_chars <= 0 or not chronological:
        return chronological

    visible = [m for m in chronological if m.role in ("user", "assistant")]

    def _line_len(m: ChatMessage) -> int:
        role = "Assistant" if m.role == "assistant" else "User"
        return len(f"{role}: {m.content}") + 1

    while visible and sum(_line_len(m) for m in visible) > max_chars:
        visible.pop(0)
    return visible


async def recent_thread_transcript(
    session: AsyncSession,
    *,
    thread_id: str,
    max_messages: int = 24,
    max_chars: int = 12000,
) -> str:
    lim = max(1, min(100, max_messages))
    rows = (
        await session.execute(
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(lim)
        )
    ).scalars().all()
    if not rows:
        return ""
    chronological = [m for m in reversed(rows) if m.role in ("user", "assistant")]
    chronological = _trim_transcript_by_chars(chronological, max_chars)
    parts: list[str] = []
    for item in chronological:
        role = "Assistant" if item.role == "assistant" else "User"
        parts.append(f"{role}: {item.content}")
    return "\n".join(parts)


async def list_chat_threads_for_user(
    session: AsyncSession, *, user_id: str, limit: int = 20, offset: int = 0
) -> tuple[list[ChatThreadSummaryResponse], bool]:
    lim = max(1, min(100, limit))
    off = max(0, offset)
    fetch = lim + 1
    rows = (
        await session.execute(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc().nulls_last(), ChatThread.created_at.desc())
            .offset(off)
            .limit(fetch)
        )
    ).scalars()
    items = list(rows)
    has_more = len(items) > lim
    if has_more:
        items = items[:lim]
    return ([_to_summary(row) for row in items], has_more)


async def get_chat_thread_for_user(
    session: AsyncSession,
    *,
    user_id: str,
    thread_id: str,
    limit: int = 50,
    before_message_id: str | None = None,
) -> ChatThreadDetailResponse | None:
    lim = max(1, min(200, limit))
    thread_row = (
        await session.execute(
            select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == user_id).limit(1)
        )
    ).scalar_one_or_none()
    if thread_row is None:
        return None

    before_created: datetime | None = None
    if before_message_id:
        ref = await session.get(ChatMessage, before_message_id)
        if ref is not None and ref.thread_id == thread_id:
            before_created = ref.created_at

    stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id)
    if before_created is not None:
        stmt = stmt.where(ChatMessage.created_at < before_created)
    stmt = stmt.order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(lim + 1)
    msg_rows = (await session.execute(stmt)).scalars().all()
    has_more = len(msg_rows) > lim
    if has_more:
        msg_rows = msg_rows[:lim]
    chronological = list(reversed(msg_rows))

    return ChatThreadDetailResponse(
        thread=_to_summary(thread_row),
        messages=[
            ChatMessageResponse(
                id=m.id,
                role="assistant" if m.role == "assistant" else ("tool" if m.role == "tool" else "user"),
                content=m.content,
                created_at=_iso(m.created_at),
            )
            for m in chronological
        ],
        has_more_messages=has_more,
    )
