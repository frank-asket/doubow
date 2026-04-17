import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.agents import AgentStatusResponse

router = APIRouter(prefix="/agents", tags=["agents"])

AGENTS: list[AgentStatusResponse] = [
    AgentStatusResponse(
        name="discovery",
        label="Discovery agent",
        description="Scans job boards and ATS portals",
        status="active",
    ),
    AgentStatusResponse(
        name="scorer",
        label="Match scorer",
        description="Computes fit scores by dimension",
        status="running",
        progress=0.62,
        message="Scoring new roles",
        items_processed=14,
    ),
    AgentStatusResponse(
        name="orchestrator",
        label="Orchestrator",
        description="Routes tasks and enforces approval gate",
        status="running",
        progress=0.34,
        message="Scheduling writer agent",
    ),
]


@router.get("/status", response_model=list[AgentStatusResponse])
async def agent_status() -> list[AgentStatusResponse]:
    return AGENTS


@router.get("/status/stream")
async def status_stream() -> StreamingResponse:
    async def event_generator():
        while True:
            for agent in AGENTS:
                payload = json.dumps(agent.model_dump(mode="json"))
                yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
