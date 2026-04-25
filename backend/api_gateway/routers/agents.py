import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.chat_thread import ChatThread
from models.user import User
from config import settings
from schemas.agents import (
    AgentStatusResponse,
    ChatThreadDetailResponse,
    ChatThreadListResponse,
    ChatThreadSummaryResponse,
    OrchestratorChatRequest,
)
from services.agent_chat_service import (
    append_chat_message,
    ensure_thread_for_user,
    get_chat_thread_for_user,
    list_chat_threads_for_user,
    recent_thread_transcript,
)
from services.agents_service import build_orchestrator_user_context, list_agent_status
from services.llm_prompts import ORCHESTRATOR_SYSTEM, normalize_orchestrator_response
from services.openrouter import stream_chat_completion_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=list[AgentStatusResponse])
async def agent_status(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> list[AgentStatusResponse]:
    return await list_agent_status(session=session, user_id=user.id)


@router.get("/status/stream")
async def status_stream(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> StreamingResponse:
    async def event_generator():
        while True:
            agents = await list_agent_status(session=session, user_id=user.id)
            for agent in agents:
                payload = json.dumps(agent.model_dump(mode="json"))
                yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat")
async def orchestrator_chat(
    payload: OrchestratorChatRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> StreamingResponse:
    """SSE stream compatible with ``streamOrchestratorChat`` in the web client (OpenRouter)."""

    logger.debug(
        "orchestrator_chat user=%s message_chars=%s",
        user.id,
        len(payload.message),
    )
    try:
        thread = await ensure_thread_for_user(session=session, user_id=user.id, thread_id=payload.thread_id)
        transcript = await recent_thread_transcript(
            session=session,
            thread_id=thread.id,
            max_messages=settings.orchestrator_chat_transcript_max_messages,
            max_chars=settings.orchestrator_chat_transcript_max_chars,
        )
        await append_chat_message(session=session, thread=thread, role="user", content=payload.message)
        await session.commit()
        user_context = await build_orchestrator_user_context(session=session, user_id=user.id)
    except Exception:
        logger.exception("orchestrator_chat setup failed user=%s", user.id)

        async def setup_error_stream():
            err = json.dumps({"delta": {"text": "(Error) Assistant is temporarily unavailable."}})
            yield f"data: {err}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(setup_error_stream(), media_type="text/event-stream")
    system_prompt = (
        f"{ORCHESTRATOR_SYSTEM}\n\n"
        "You are given live pipeline context from the user's account. Use it directly; do not claim you lack access.\n"
        f"{user_context}"
    )
    if transcript.strip():
        user_message = (
            "Conversation so far:\n"
            f"{transcript}\n\n"
            "Latest user message:\n"
            f"{payload.message}"
        )
    else:
        user_message = payload.message

    async def reply_stream():
        acc = ""
        try:
            meta = json.dumps({"meta": {"thread_id": thread.id}})
            yield f"data: {meta}\n\n"
            async for fragment in stream_chat_completion_chunks(
                user_message=user_message,
                system_message=system_prompt,
                use_case="chat",
            ):
                acc += fragment
            normalized = normalize_orchestrator_response(acc)
            chunk = json.dumps({"delta": {"text": normalized}})
            yield f"data: {chunk}\n\n"
            row = await session.get(ChatThread, thread.id)
            if row is not None and row.user_id == user.id:
                await append_chat_message(session=session, thread=row, role="assistant", content=normalized)
                await session.commit()
            yield "data: [DONE]\n\n"
        except RuntimeError as exc:
            err = json.dumps({"delta": {"text": f"(Configure OpenRouter.) {exc}"}})
            yield f"data: {err}\n\n"
            yield "data: [DONE]\n\n"
        except Exception:
            logger.exception("orchestrator_chat stream failed user=%s", user.id)
            err = json.dumps({"delta": {"text": "(Error) Could not complete response."}})
            yield f"data: {err}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(reply_stream(), media_type="text/event-stream")


@router.get("/chat/threads", response_model=ChatThreadListResponse)
async def list_chat_threads(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ChatThreadListResponse:
    threads, has_more = await list_chat_threads_for_user(
        session=session, user_id=user.id, limit=limit, offset=offset
    )
    return ChatThreadListResponse(threads=threads, has_more=has_more)


@router.get("/chat/threads/{thread_id}", response_model=ChatThreadDetailResponse)
async def get_chat_thread(
    thread_id: str,
    limit: int = Query(50, ge=1, le=200),
    before_message_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> ChatThreadDetailResponse:
    row = await get_chat_thread_for_user(
        session=session,
        user_id=user.id,
        thread_id=thread_id,
        limit=limit,
        before_message_id=before_message_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return row
