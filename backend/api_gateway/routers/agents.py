import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.generative_quality_rubric import assess_generative_text
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
from services.agent_action_executor import execute_action, infer_action_from_message
from services.llm_prompts import ORCHESTRATOR_SYSTEM, normalize_orchestrator_response_with_meta
from services.metrics import observe_llm_output_quality
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
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_authenticated_user),
) -> StreamingResponse:
    """SSE stream compatible with ``streamOrchestratorChat`` in the web client (OpenRouter)."""

    logger.debug(
        "orchestrator_chat user=%s message_chars=%s request_id=%s",
        user.id,
        len(payload.message),
        getattr(request.state, "request_id", "-"),
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
        logger.exception(
            "orchestrator_chat setup failed user=%s request_id=%s",
            user.id,
            getattr(request.state, "request_id", "-"),
        )

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

    action_call = infer_action_from_message(payload.message)

    async def reply_stream():
        acc = ""
        try:
            meta = json.dumps({"meta": {"thread_id": thread.id}})
            yield f"data: {meta}\n\n"
            if action_call is not None:
                tool_call_payload = {
                    "kind": "tool_call",
                    "name": action_call.action,
                    "arguments": {"limit": action_call.limit},
                }
                tool_call_evt = json.dumps(
                    {"tool_call": {"name": action_call.action, "arguments": {"limit": action_call.limit}}}
                )
                yield f"data: {tool_call_evt}\n\n"
                row = await session.get(ChatThread, thread.id)
                if row is not None and row.user_id == user.id:
                    await append_chat_message(
                        session=session,
                        thread=row,
                        role="tool",
                        content=json.dumps(tool_call_payload),
                    )
                action_result = await execute_action(session=session, user_id=user.id, call=action_call)
                observe_llm_output_quality(use_case="chat", outcome=f"action_{action_result.action}")
                tool_result_payload = {
                    "kind": "tool_result",
                    "name": action_result.action,
                    "ok": True,
                    "summary": "Action executed successfully.",
                }
                tool_result_evt = json.dumps(
                    {
                        "tool_result": {
                            "name": action_result.action,
                            "ok": True,
                            "summary": "Action executed successfully.",
                        }
                    }
                )
                yield f"data: {tool_result_evt}\n\n"
                row = await session.get(ChatThread, thread.id)
                if row is not None and row.user_id == user.id:
                    await append_chat_message(
                        session=session,
                        thread=row,
                        role="tool",
                        content=json.dumps(tool_result_payload),
                    )
                chunk = json.dumps({"delta": {"text": action_result.response_text}})
                yield f"data: {chunk}\n\n"
                row = await session.get(ChatThread, thread.id)
                if row is not None and row.user_id == user.id:
                    await append_chat_message(
                        session=session, thread=row, role="assistant", content=action_result.response_text
                    )
                    await session.commit()
                yield "data: [DONE]\n\n"
                return
            async for fragment in stream_chat_completion_chunks(
                user_message=user_message,
                system_message=system_prompt,
                use_case="chat",
            ):
                acc += fragment
            if not acc.strip():
                observe_llm_output_quality(use_case="chat", outcome="empty_raw")
            normalized, was_normalized = normalize_orchestrator_response_with_meta(acc)
            observe_llm_output_quality(
                use_case="chat",
                outcome="normalized" if was_normalized else "already_structured",
            )
            rubric = assess_generative_text(normalized, use_case="chat")
            observe_llm_output_quality(
                use_case="chat",
                outcome="rubric_pass" if rubric.passed else "rubric_fail",
            )
            if not rubric.passed:
                for v in rubric.violations[:3]:
                    observe_llm_output_quality(use_case="chat", outcome=f"violation_{v.split(' ')[0][:24]}")
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
            logger.exception(
                "orchestrator_chat stream failed user=%s request_id=%s",
                user.id,
                getattr(request.state, "request_id", "-"),
            )
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
