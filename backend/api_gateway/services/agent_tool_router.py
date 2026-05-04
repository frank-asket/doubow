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
    trigger_catalog_refresh: bool | None = None
    persist_feedback_learning: bool | None = None
    catalog_preset: str | None = None
    include_legacy_connectors: bool | None = None
    include_scrapling: bool | None = None
    resume_aligned_catalog: bool | None = None
    pipeline_stages: list[str] | None = None


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
        "- trigger_catalog_refresh: boolean or null — only for run_job_search_pipeline.\n"
        "- persist_feedback_learning: boolean or null — only for run_job_search_pipeline.\n"
        '- catalog_preset: "hourly" or "daily" or null — only when triggering catalog refresh.\n'
        "- include_legacy_connectors: boolean or null — catalog ingest option.\n"
        "- include_scrapling: boolean or null — only for run_job_search_pipeline with catalog refresh; Scrapling step.\n"
        "- resume_aligned_catalog: boolean or null — catalog ingest option.\n"
        "- pipeline_stages: array of stage id strings or null — omit for default full pipeline.\n"
        "Choose `none` when the user is asking for advice, explanation, or editing prose — not an account action.\n\n"
        "Tools:\n"
        f"{catalog}"
    )
    try:
        raw = await chat_completion(
            user_message=user_message.strip(),
            system_message=system,
            use_case="drafts",
            max_tokens=320,
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

    call_kwargs: dict = {
        "action": cast(AgentActionName, act),
        "limit": plan.limit,
        "application_id": plan.application_id,
        "job_id": plan.job_id,
        "approval_id": plan.approval_id,
        "channel": cast(AgentChannel | None, channel_valid),
    }
    if plan.trigger_catalog_refresh is not None:
        call_kwargs["trigger_catalog_refresh"] = plan.trigger_catalog_refresh
    if plan.persist_feedback_learning is not None:
        call_kwargs["persist_feedback_learning"] = plan.persist_feedback_learning
    cp = (plan.catalog_preset or "").strip().lower()
    if cp in {"hourly", "daily"}:
        call_kwargs["catalog_preset"] = cp
    if plan.include_legacy_connectors is not None:
        call_kwargs["include_legacy_connectors"] = plan.include_legacy_connectors
    if plan.include_scrapling is not None:
        call_kwargs["include_scrapling"] = plan.include_scrapling
    if plan.resume_aligned_catalog is not None:
        call_kwargs["resume_aligned_catalog"] = plan.resume_aligned_catalog
    if plan.pipeline_stages is not None:
        call_kwargs["pipeline_stages"] = plan.pipeline_stages

    return AgentActionCall(**call_kwargs)
