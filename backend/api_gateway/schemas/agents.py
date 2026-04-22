from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["discovery", "scorer", "tailor", "writer", "apply", "prep", "monitor", "orchestrator"]
AgentStatus = Literal["active", "running", "idle", "error"]


class AgentStatusResponse(BaseModel):
    name: AgentName
    label: str
    description: str
    status: AgentStatus
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    message: str | None = None
    items_processed: int | None = None


class OrchestratorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=16_000)
