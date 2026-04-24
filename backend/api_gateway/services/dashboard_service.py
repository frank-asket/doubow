from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.approval import Approval
from models.job_score import JobScore
from models.user import User
from schemas.dashboard import DashboardSummaryResponse

HIGH_FIT_THRESHOLD = 4.0

# Submitted = user sent an application; responded = progressed to a stage implying employer reply.
_SUBMITTED_STATUSES = ("applied", "interview", "offer", "rejected")
_REPLIED_STATUSES = ("interview", "offer", "rejected")


def _utc_start_of_iso_week() -> datetime:
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    monday = (now - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return monday


async def get_dashboard_summary(session: AsyncSession, user_id: str) -> DashboardSummaryResponse:
    user_row = await session.get(User, user_id)
    profile_views: int | None = user_row.profile_views if user_row else None

    total_scored = (
        await session.execute(select(func.count()).select_from(JobScore).where(JobScore.user_id == user_id))
    ).scalar_one()
    total_scored_int = int(total_scored)

    high_fit = (
        await session.execute(
            select(func.count())
            .select_from(JobScore)
            .where(JobScore.user_id == user_id, JobScore.fit_score >= HIGH_FIT_THRESHOLD)
        )
    ).scalar_one()

    week_start = _utc_start_of_iso_week()
    evaluated_week = (
        await session.execute(
            select(func.count())
            .select_from(JobScore)
            .where(JobScore.user_id == user_id, JobScore.scored_at >= week_start)
        )
    ).scalar_one()

    avg_row = (
        await session.execute(select(func.avg(JobScore.fit_score)).where(JobScore.user_id == user_id))
    ).scalar_one()
    avg_fit: float | None
    if avg_row is None:
        avg_fit = None
    else:
        avg_fit = round(float(avg_row), 2)

    pipeline_count = (
        await session.execute(
            select(func.count()).select_from(Application).where(Application.user_id == user_id)
        )
    ).scalar_one()

    pending_appr = (
        await session.execute(
            select(func.count())
            .select_from(Approval)
            .where(Approval.user_id == user_id, Approval.status == "pending")
        )
    ).scalar_one()

    applied_awaiting = (
        await session.execute(
            select(func.count())
            .select_from(Application)
            .where(
                Application.user_id == user_id,
                Application.status.in_(["pending", "applied", "interview"]),
            )
        )
    ).scalar_one()

    submitted_ct = (
        await session.execute(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id, Application.status.in_(_SUBMITTED_STATUSES))
        )
    ).scalar_one()
    replied_ct = (
        await session.execute(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id, Application.status.in_(_REPLIED_STATUSES))
        )
    ).scalar_one()
    submitted_int = int(submitted_ct)
    response_rate_pct: int | None
    if submitted_int == 0:
        response_rate_pct = None
    else:
        response_rate_pct = int(round(100 * int(replied_ct) / submitted_int))

    return DashboardSummaryResponse(
        high_fit_count=int(high_fit),
        pipeline_count=int(pipeline_count),
        pending_approvals=int(pending_appr),
        evaluated_this_week=int(evaluated_week),
        avg_fit_score=avg_fit,
        applied_awaiting_reply=int(applied_awaiting),
        total_scored_jobs=total_scored_int,
        profile_views=profile_views,
        response_rate_pct=response_rate_pct,
    )
