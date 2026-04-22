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
from services.agents_service import list_agent_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

_ORCH_STUB_REPLY = (
    "Orchestrator chat is not fully wired to a model yet. "
    "Use Pipeline to generate drafts and Approvals to review them."
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
    user: User = Depends(get_authenticated_user),
) -> StreamingResponse:
    """SSE stream compatible with ``streamOrchestratorChat`` in the web client."""

    async def reply_stream():
        chunk = json.dumps({"delta": {"text": _ORCH_STUB_REPLY}})
        yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    logger.debug(
        "orchestrator_chat user=%s message_chars=%s",
        user.id,
        len(payload.message),
    )
    return StreamingResponse(reply_stream(), media_type="text/event-stream")
