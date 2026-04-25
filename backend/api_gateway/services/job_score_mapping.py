"""ORM job_scores → API JobScore schema."""

from __future__ import annotations

from models.job_score import JobScore as JobScoreRow
from schemas.jobs import Channel, DimensionScores, JobScore as JobScoreSchema


def _clamp_dim(value: object, default: float = 3.0) -> float:
    try:
        x = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return max(0.0, min(5.0, x))


def _clamp_fit(value: object) -> float:
    try:
        x = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 3.0
    return max(1.0, min(5.0, x))


def _dimension_scores(raw: dict) -> DimensionScores:
    return DimensionScores(
        tech=_clamp_dim(raw.get("tech", 3.0)),
        culture=_clamp_dim(raw.get("culture", 3.0)),
        seniority=_clamp_dim(raw.get("seniority", 3.0)),
        comp=_clamp_dim(raw.get("comp", 3.0)),
        location=_clamp_dim(raw.get("location", 3.0)),
    )


def _channel(raw: dict) -> Channel:
    ch = raw.get("channel_recommendation", "email")
    if ch in ("email", "linkedin", "company_site"):
        return ch  # type: ignore[return-value]
    return "email"


def job_score_to_api(job_id: str, row: JobScoreRow | None) -> JobScoreSchema | None:
    if row is None:
        return None
    dims_raw = row.dimension_scores if isinstance(row.dimension_scores, dict) else {}
    return JobScoreSchema(
        job_id=job_id,
        fit_score=_clamp_fit(row.fit_score),
        fit_reasons=list(row.fit_reasons or []),
        risk_flags=list(row.risk_flags or []),
        dimension_scores=_dimension_scores(dims_raw),
        channel_recommendation=_channel(dims_raw),
        scored_at=row.scored_at,
    )
