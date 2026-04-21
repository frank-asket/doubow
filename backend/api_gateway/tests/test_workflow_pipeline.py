import pytest

from workflow.pipeline import PipelineStage, derive_application_pipeline_stage


@pytest.mark.parametrize(
    ("has_job_score", "application_status", "approval_status", "expected"),
    [
        (False, "pending", None, PipelineStage.SCORE),
        (True, "pending", None, PipelineStage.DRAFT),
        (True, "pending", "pending", PipelineStage.APPROVE),
        (True, "pending", "approved", PipelineStage.SEND_PREP),
        (True, "pending", "edited", PipelineStage.SEND_PREP),
        (True, "applied", "approved", PipelineStage.SEND_PREP),
        (True, "interview", None, PipelineStage.SEND_PREP),
        (True, "offer", None, PipelineStage.SEND_PREP),
        (True, "rejected", None, PipelineStage.SEND_PREP),
        (True, "pending", "weird", PipelineStage.DRAFT),
    ],
)
def test_derive_application_pipeline_stage(
    has_job_score: bool,
    application_status: str,
    approval_status: str | None,
    expected: PipelineStage,
) -> None:
    assert (
        derive_application_pipeline_stage(
            has_job_score=has_job_score,
            application_status=application_status,
            approval_status=approval_status,
        )
        == expected
    )
