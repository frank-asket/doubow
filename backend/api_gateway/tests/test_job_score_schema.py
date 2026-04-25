"""Guarantees ORM → API JobScore mapping always satisfies the public Pydantic schema (TASK-020)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from models.job_score import JobScore as JobScoreRow
from schemas.jobs import JobScore as JobScoreSchema
from services.job_score_mapping import job_score_to_api


def _row(
    *,
    job_id: str = "job-1",
    fit_score: float = 4.0,
    fit_reasons: list[str] | None = None,
    risk_flags: list[str] | None = None,
    dimension_scores: dict | None = None,
) -> JobScoreRow:
    return JobScoreRow(
        id="score-row-1",
        user_id="user-1",
        job_id=job_id,
        fit_score=fit_score,
        fit_reasons=fit_reasons or [],
        risk_flags=risk_flags or [],
        dimension_scores=dimension_scores or {},
        scored_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_job_score_to_api_none_when_missing_row() -> None:
    assert job_score_to_api("job-x", None) is None


def test_job_score_to_api_round_trip_passes_job_score_schema() -> None:
    row = _row(
        dimension_scores={
            "tech": 4.1,
            "culture": 3.9,
            "seniority": 4.0,
            "comp": 3.5,
            "location": 4.2,
            "channel_recommendation": "linkedin",
        },
    )
    api = job_score_to_api("job-1", row)
    assert api is not None
    JobScoreSchema.model_validate(api.model_dump())


def test_fit_score_clamped_to_schema_bounds() -> None:
    low = job_score_to_api("j", _row(job_id="j", fit_score=0.0))
    high = job_score_to_api("j2", _row(job_id="j2", fit_score=9.9))
    assert low is not None and high is not None
    assert low.fit_score == 1.0
    assert high.fit_score == 5.0
    JobScoreSchema.model_validate(low.model_dump())
    JobScoreSchema.model_validate(high.model_dump())


def test_dimension_scores_clamped_and_defaults() -> None:
    api = job_score_to_api(
        "jid",
        _row(
            job_id="jid",
            dimension_scores={
                "tech": 99.0,
                "culture": -10.0,
                "channel_recommendation": "email",
            },
        ),
    )
    assert api is not None
    assert api.dimension_scores.tech == 5.0
    assert api.dimension_scores.culture == 0.0
    assert api.dimension_scores.seniority == 3.0
    JobScoreSchema.model_validate(api.model_dump())


def test_invalid_channel_recommendation_falls_back_to_email() -> None:
    api = job_score_to_api(
        "jid",
        _row(dimension_scores={"channel_recommendation": "carrier_pigeon"}),
    )
    assert api is not None
    assert api.channel_recommendation == "email"


def test_non_object_dimension_scores_uses_defaults() -> None:
    base = _row()
    row = SimpleNamespace(
        fit_score=base.fit_score,
        fit_reasons=base.fit_reasons,
        risk_flags=base.risk_flags,
        dimension_scores="not-a-dict",
        scored_at=base.scored_at,
    )
    api = job_score_to_api("jid", row)  # type: ignore[arg-type]
    assert api is not None
    assert api.dimension_scores.tech == 3.0
    JobScoreSchema.model_validate(api.model_dump())


def test_schema_rejects_out_of_range_fit_if_constructed_directly() -> None:
    with pytest.raises(ValidationError):
        JobScoreSchema(
            job_id="x",
            fit_score=0.5,
            fit_reasons=[],
            risk_flags=[],
            dimension_scores={"tech": 3, "culture": 3, "seniority": 3, "comp": 3, "location": 3},
            channel_recommendation="email",
            scored_at=datetime.now(timezone.utc),
        )
