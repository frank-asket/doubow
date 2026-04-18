import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from dependencies import get_current_user_id
from schemas.agents import AgentStatusResponse
from services.agents_service import list_agent_status

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=list[AgentStatusResponse])
async def agent_status(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> list[AgentStatusResponse]:
    return await list_agent_status(session=session, user_id=user_id)


@router.get("/status/stream")
async def status_stream(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    async def event_generator():
        while True:
            agents = await list_agent_status(session=session, user_id=user_id)
            for agent in agents:
                payload = json.dumps(agent.model_dump(mode="json"))
                yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
