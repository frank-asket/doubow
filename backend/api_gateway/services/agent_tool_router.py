"""LLM-assisted routing from natural language to structured agent actions (agent-native parity layer)."""

from __future__ import annotations

import json
import logging
import re

from typing import cast

from pydantic import BaseModel, Field

from config import settings
from services.agent_action_executor import AgentActionCall, AgentActionName, AgentChannel
from services.agent_tools_catalog import AGENT_TOOLS
from services.metrics import observe_assistant_tool_routing
from services.openrouter import chat_completion

logger = logging.getLogger(__name__)

_VALID_NAMES = frozenset(t.name for t in AGENT_TOOLS)


class _ToolPlanRaw(BaseModel):
    action: str = Field(
        description="One of the tool names, or 'none' for general chat (no tool).",
    )
    limit: int = Field(default=5, ge=1, le=20)
    application_id: str | None = None
    job_id: str | None = None
    approval_id: str | None = None
    channel: str | None = Field(
        default=None,
        description="email, linkedin, or company_site — only for queue_job_to_pipeline.",
    )


def _extract_json_object(text: str) -> str | None:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        return None
    return m.group(0)


async def plan_agent_action_from_llm(user_message: str) -> AgentActionCall | None:
    """When keyword routing misses, ask a small model which tool applies (or none)."""
    if not settings.openrouter_api_key:
        observe_assistant_tool_routing(phase="llm_skipped_no_key")
        return None
    if not settings.orchestrator_llm_tool_routing:
        observe_assistant_tool_routing(phase="llm_skipped_flag")
        return None

    catalog = "\n".join(f"- {t.name}: {t.summary}" for t in AGENT_TOOLS)
    system = (
        "You route user messages to Doubow assistant tools. "
        "Reply with ONLY a JSON object (no markdown), keys:\n"
        '- action: string — must be one tool name from the list below, or the literal word "none".\n'
        "- limit: integer 1–20 — only for tools that list rows (default 5).\n"
        '- application_id: string or null — app_* id or UUID when the tool needs a specific application.\n'
        "- job_id: string or null — jb_* id or job UUID for queue/dismiss actions.\n"
        "- approval_id: string or null — approval UUID for approve/reject actions.\n"
        '- channel: string or null — "email", "linkedin", or "company_site" when queueing a job.\n'
        "Choose `none` when the user is asking for advice, explanation, or editing prose — not an account action.\n\n"
        "Tools:\n"
        f"{catalog}"
    )
    try:
        raw = await chat_completion(
            user_message=user_message.strip(),
            system_message=system,
            use_case="drafts",
            max_tokens=220,
        )
    except Exception:
        logger.exception("agent_tool_router: OpenRouter call failed")
        observe_assistant_tool_routing(phase="llm_plan_error")
        return None

    blob = _extract_json_object(raw)
    if not blob:
        observe_assistant_tool_routing(phase="llm_plan_none")
        return None
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        logger.debug("agent_tool_router: invalid json raw=%s", raw[:200])
        observe_assistant_tool_routing(phase="llm_plan_none")
        return None

    try:
        plan = _ToolPlanRaw.model_validate(data)
    except Exception:
        observe_assistant_tool_routing(phase="llm_plan_none")
        return None

    act = (plan.action or "").strip()
    if act.lower() == "none" or not act:
        observe_assistant_tool_routing(phase="llm_plan_none")
        return None
    if act not in _VALID_NAMES:
        logger.debug("agent_tool_router: unknown action=%s", act)
        observe_assistant_tool_routing(phase="llm_plan_none")
        return None

    ch_norm = (plan.channel or "").strip().lower()
    channel_valid: str | None = None
    if ch_norm in {"email", "linkedin", "company_site"}:
        channel_valid = ch_norm

    observe_assistant_tool_routing(phase="llm_plan_hit")

    return AgentActionCall(
        action=cast(AgentActionName, act),
        limit=plan.limit,
        application_id=plan.application_id,
        job_id=plan.job_id,
        approval_id=plan.approval_id,
        channel=cast(AgentChannel | None, channel_valid),
    )
