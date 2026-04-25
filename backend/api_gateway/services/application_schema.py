"""Map persistence rows into API ``Application`` payloads (including derived pipeline stage)."""

from models.application import Application
from models.approval import Approval
from models.job import Job
from models.job_score import JobScore as JobScoreRow
from schemas.applications import Application as ApplicationSchema
from schemas.jobs import Job as JobSchema
from services.job_score_mapping import job_score_to_api
from workflow.pipeline import derive_application_pipeline_stage

_ALLOWED_APP_STATUSES = {"saved", "pending", "applied", "interview", "offer", "rejected"}
_ALLOWED_CHANNELS = {"email", "linkedin", "company_site"}
_ALLOWED_JOB_SOURCES = {"ashby", "greenhouse", "lever", "linkedin", "wellfound", "manual", "catalog"}


def _safe_status(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_APP_STATUSES else "pending"


def _safe_channel(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_CHANNELS else "email"


def _safe_job_source(raw: object) -> str:
    s = str(raw or "").strip().lower()
    return s if s in _ALLOWED_JOB_SOURCES else "manual"


def application_to_schema(
    app: Application,
    job: Job,
    score_row: JobScoreRow | None,
    *,
    approval: Approval | None = None,
) -> ApplicationSchema:
    pipeline_stage = derive_application_pipeline_stage(
        has_job_score=score_row is not None,
        application_status=app.status,
        approval_status=approval.status if approval else None,
    )
    return ApplicationSchema(
        id=app.id,
        user_id=app.user_id,
        job=JobSchema(
            id=job.id,
            source=_safe_job_source(job.source),  # type: ignore[arg-type]
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location or "Remote",
            salary_range=job.salary_range,
            description=job.description or "",
            url=job.url or "",
            posted_at=job.posted_at,
            discovered_at=job.discovered_at,
        ),
        score=job_score_to_api(job.id, score_row),
        status=_safe_status(app.status),  # type: ignore[arg-type]
        channel=_safe_channel(app.channel),  # type: ignore[arg-type]
        applied_at=app.applied_at,
        last_updated=app.last_updated,
        idempotency_key=app.idempotency_key,
        notes=app.notes,
        is_stale=app.is_stale,
        dedup_group=app.dedup_group,
        pipeline_stage=pipeline_stage,
    )
