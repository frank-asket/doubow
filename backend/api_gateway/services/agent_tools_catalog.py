"""Agent-native tool definitions — single source for prompts, routing validation, and capability discovery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentToolSpec:
    name: str
    summary: str


# Keep aligned with ``AgentActionName`` in ``agent_action_executor``.
AGENT_TOOLS: tuple[AgentToolSpec, ...] = (
    AgentToolSpec(
        "get_pipeline_snapshot",
        "Summarize application counts by status, pending approvals, and recent pipeline rows.",
    ),
    AgentToolSpec(
        "list_pending_approvals",
        "List pending outbound drafts awaiting human approval (optional limit 1–20).",
    ),
    AgentToolSpec(
        "get_job_matches",
        "Show top scored job matches from Discover for this profile (optional limit).",
    ),
    AgentToolSpec(
        "get_application_detail",
        "Deep dive on one application (by app_* id or UUID) or the most recently updated application.",
    ),
    AgentToolSpec(
        "create_draft_for_application",
        "Create a new draft approval (email/LinkedIn) for a specific application_id when policy allows.",
    ),
    AgentToolSpec(
        "recompute_job_scores",
        "Refresh all job fit scores for the current profile (after resume or preference changes).",
    ),
    AgentToolSpec(
        "get_resume_profile_snapshot",
        "Summarize the latest parsed resume and job-search preferences on file.",
    ),
    AgentToolSpec(
        "get_prep_session_summary",
        "Summarize the latest or application-specific interview prep (questions, STAR stories, company brief).",
    ),
    AgentToolSpec(
        "generate_prep_for_application",
        "Regenerate full interview prep for an application (LLM-heavy; same as Prep > Generate in the app).",
    ),
    AgentToolSpec(
        "list_recent_autopilot_runs",
        "List recent autopilot / batch runs (status, scope, failure hints).",
    ),
    AgentToolSpec(
        "queue_job_to_pipeline",
        "Queue a catalog job into your pipeline (Discover → Application); requires job_id and channel (email/linkedin/company_site).",
    ),
    AgentToolSpec(
        "dismiss_job_from_discover",
        "Dismiss/hide a job from your Discover matches (same as swipe dismiss).",
    ),
    AgentToolSpec(
        "approve_outbound_draft",
        "Approve a pending outbound draft (approval UUID); triggers the same send pipeline as the Approvals UI.",
    ),
    AgentToolSpec(
        "reject_outbound_draft",
        "Reject/delete a pending approval draft without sending.",
    ),
)


def format_agent_tools_for_user_context() -> str:
    """Appended to orchestrator system context so the model knows what the assistant can do."""
    lines = [f"- {t.name}: {t.summary}" for t in AGENT_TOOLS]
    return "Assistant can also run these account actions (same outcomes as the product UI):\n" + "\n".join(lines)


def tools_for_json_router_prompt() -> str:
    """Compact catalog for the tool-routing model."""
    return "\n".join(f"- {t.name}: {t.summary}" for t in AGENT_TOOLS)
