"""Outcome-derived feedback for the job-search pipeline (hints + optional preference snapshot).

Scoring still uses server-side blend weights unless product code reads ``feedback_learning.matching_blend_hints``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Align with schemas.applications.ApplicationStatus
_KNOWN_STATUSES = frozenset({"saved", "pending", "applied", "interview", "offer", "rejected"})


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_feedback_snapshot(
    applications_by_status: dict[str, int],
    *,
    trace_id: str | None = None,
    prior_feedback_learning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize application outcomes and propose small matching-blend nudges (advisory).

    ``prior_feedback_learning`` is merged shallowly for continuity (e.g. prior notes).
    """
    counts = {k: int(v) for k, v in applications_by_status.items() if int(v) > 0}
    total = sum(counts.values())

    def _n(status: str) -> int:
        return int(counts.get(status, 0))

    offer_n = _n("offer")
    interview_n = _n("interview")
    applied_n = _n("applied")
    pending_n = _n("pending")
    saved_n = _n("saved")
    rejected_n = _n("rejected")

    interview_or_offer = interview_n + offer_n
    active_pipeline = saved_n + pending_n + applied_n

    offer_rate = offer_n / total if total else 0.0
    rejection_rate = rejected_n / total if total else 0.0
    interview_rate = interview_n / total if total else 0.0
    progression_rate = interview_or_offer / total if total else 0.0

    # Funnel: saved → … → offer (coarse)
    denom_push = saved_n + applied_n + interview_n + offer_n + rejected_n
    apply_conversion = applied_n / denom_push if denom_push else 0.0

    notes: list[str] = []
    if total == 0:
        notes.append("No applications yet — feedback will sharpen once you queue and track outcomes.")
    else:
        if saved_n > applied_n * 2 and saved_n >= 3:
            notes.append(
                "Many roles stay in “saved” vs “applied” — consider prioritizing a smaller set and applying sooner."
            )
        if rejection_rate >= 0.45 and total >= 4 and progression_rate < 0.2:
            notes.append(
                "High rejection share with limited interviews — tighten role/title fit or refine keywords before widening search."
            )
        if interview_rate >= 0.15 and offer_rate < 0.05 and total >= 5:
            notes.append(
                "Interviews are landing but offers are rare — revisit compensation signals and closing narrative."
            )
        if offer_rate >= 0.1 and total >= 3:
            notes.append("Strong offer signal vs pipeline size — current targeting is working; consider selective expansion.")

    # Advisory deltas for a future per-user blend (not applied automatically).
    sem_d = lex_d = llm_d = 0.0
    rationale_parts: list[str] = []
    if total >= 3:
        if progression_rate >= 0.25:
            sem_d += 0.03
            rationale_parts.append("Healthy interview/offer progression → slight trust in semantic similarity.")
        if rejection_rate >= 0.4 and progression_rate <= 0.15:
            lex_d += 0.05
            sem_d -= 0.02
            rationale_parts.append("Many rejections, few advances → favor keyword/title alignment vs breadth.")
        if saved_n >= 5 and apply_conversion < 0.25:
            llm_d += 0.02
            rationale_parts.append("Low apply-through from saved queue → optional LLM fit signal to prioritize order.")

    sem_d = _clamp(sem_d, -0.1, 0.1)
    lex_d = _clamp(lex_d, -0.1, 0.1)
    llm_d = _clamp(llm_d, -0.1, 0.1)

    snapshot: dict[str, Any] = {
        "version": 1,
        "updated_at": datetime.now(UTC).isoformat(),
        "trace_id": trace_id,
        "totals": {"applications_tracked": total, "active_pipeline": active_pipeline},
        "counts": counts,
        "rates": {
            "offer_rate": round(offer_rate, 4),
            "rejection_rate": round(rejection_rate, 4),
            "interview_rate": round(interview_rate, 4),
            "interview_or_offer_rate": round(progression_rate, 4),
            "apply_conversion": round(apply_conversion, 4),
        },
        "insights": notes,
        "matching_blend_hints": {
            "semantic_matching_delta": round(sem_d, 4),
            "lexical_matching_delta": round(lex_d, 4),
            "llm_job_matching_delta": round(llm_d, 4),
            "rationale": "; ".join(rationale_parts) if rationale_parts else "Insufficient outcome depth for nudges.",
        },
        "unknown_status_keys": sorted(k for k in counts if k not in _KNOWN_STATUSES),
    }

    if prior_feedback_learning and isinstance(prior_feedback_learning, dict):
        prev_notes = prior_feedback_learning.get("historical_notes")
        if isinstance(prev_notes, list) and prev_notes:
            snapshot["historical_notes"] = prev_notes[-5:]

    return snapshot

