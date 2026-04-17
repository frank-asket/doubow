from schemas.agents import AgentStatusResponse


async def list_agent_status() -> list[AgentStatusResponse]:
    return [
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
