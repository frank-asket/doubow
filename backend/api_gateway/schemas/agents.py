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
    thread_id: str | None = None


class ChatThreadSummaryResponse(BaseModel):
    id: str
    title: str
    updated_at: str
    created_at: str


class ChatMessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant", "tool"]
    content: str
    created_at: str


class ChatThreadDetailResponse(BaseModel):
    thread: ChatThreadSummaryResponse
    messages: list[ChatMessageResponse]
    has_more_messages: bool = False


class ChatThreadListResponse(BaseModel):
    threads: list[ChatThreadSummaryResponse]
    has_more: bool = False
