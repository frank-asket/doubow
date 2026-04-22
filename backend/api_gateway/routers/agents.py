import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_authenticated_user
from models.user import User
from schemas.agents import AgentStatusResponse, OrchestratorChatRequest
from services.agents_service import build_orchestrator_user_context, list_agent_status
from services.openrouter import stream_chat_completion_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

_ORCH_SYSTEM = (
    "You are Doubow's orchestrator agent. Help with job search strategy, pipeline prioritization, "
    "drafts and approvals, and interview prep. Be concise and actionable."
)


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
    user_context = await build_orchestrator_user_context(session=session, user_id=user.id)
    system_prompt = (
        f"{_ORCH_SYSTEM}\n\n"
        "You are given live pipeline context from the user's account. Use it directly; do not claim you lack access.\n"
        f"{user_context}"
    )

    async def reply_stream():
        try:
            async for fragment in stream_chat_completion_chunks(
                user_message=payload.message,
                system_message=system_prompt,
            ):
                chunk = json.dumps({"delta": {"text": fragment}})
                yield f"data: {chunk}\n\n"
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
