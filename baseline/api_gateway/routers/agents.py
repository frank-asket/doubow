import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.agents import AgentStatusResponse
from services.agents_service import list_agent_status

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=list[AgentStatusResponse])
async def agent_status() -> list[AgentStatusResponse]:
    return await list_agent_status()


@router.get("/status/stream")
async def status_stream() -> StreamingResponse:
    async def event_generator():
        while True:
            agents = await list_agent_status()
            for agent in agents:
                payload = json.dumps(agent.model_dump(mode="json"))
                yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
