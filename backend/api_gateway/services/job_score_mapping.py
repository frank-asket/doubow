"""ORM job_scores → API JobScore schema."""

from models.job_score import JobScore as JobScoreRow
from schemas.jobs import Channel, DimensionScores, JobScore as JobScoreSchema


def _dimension_scores(raw: dict) -> DimensionScores:
    return DimensionScores(
        tech=float(raw.get("tech", 3.0)),
        culture=float(raw.get("culture", 3.0)),
        seniority=float(raw.get("seniority", 3.0)),
        comp=float(raw.get("comp", 3.0)),
        location=float(raw.get("location", 3.0)),
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
        fit_score=float(row.fit_score),
        fit_reasons=list(row.fit_reasons or []),
        risk_flags=list(row.risk_flags or []),
        dimension_scores=_dimension_scores(dims_raw),
        channel_recommendation=_channel(dims_raw),
        scored_at=row.scored_at,
    )
