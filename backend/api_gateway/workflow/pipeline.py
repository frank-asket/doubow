"""Product pipeline as explicit stages backed by Postgres state.

Maps the flow discover → score → draft → approve → send/prep to rows and columns
already stored for applications, scores, and approvals — no LangGraph runtime.

Branching:
  - Approval rejected (deleted row): back toward draft/score depending on score presence.
  - CRM outcomes (interview / offer / rejected): terminal from the automation pipeline's view.
"""

from __future__ import annotations

from enum import StrEnum


class PipelineStage(StrEnum):
    SCORE = "score"
    DRAFT = "draft"
    APPROVE = "approve"
    SEND_PREP = "send_prep"


_TERMINAL_APPLICATION_STATUSES = frozenset({"interview", "offer", "rejected"})
_APPROVED_APPROVAL_STATUSES = frozenset({"approved", "edited"})


def derive_application_pipeline_stage(
    *,
    has_job_score: bool,
    application_status: str,
    approval_status: str | None,
) -> PipelineStage:
    """Infer current pipeline stage from persisted application and approval fields."""
    if application_status in _TERMINAL_APPLICATION_STATUSES:
        return PipelineStage.SEND_PREP

    if not has_job_score:
        return PipelineStage.SCORE

    if approval_status is None:
        return PipelineStage.DRAFT

    if approval_status == "pending":
        return PipelineStage.APPROVE

    if approval_status in _APPROVED_APPROVAL_STATUSES:
        return PipelineStage.SEND_PREP

    # Unknown status — treat as draft work still outstanding.
    return PipelineStage.DRAFT
