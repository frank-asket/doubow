from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import Job
from models.job_alert_delivery import JobAlertDelivery
from models.job_alert_subscription import JobAlertSubscription
from models.job_dismissal import JobDismissal
from models.job_score import JobScore
from models.user import User
from schemas.job_alerts import (
    JobAlertFeedItem,
    JobAlertFeedResponse,
    JobAlertSettingsPatch,
    JobAlertSettingsResponse,
)
from services.outbound_email import send_email_outbound

logger = logging.getLogger(__name__)


def _to_settings_response(sub: JobAlertSubscription) -> JobAlertSettingsResponse:
    return JobAlertSettingsResponse(
        enabled=bool(sub.enabled),
        frequency=str(sub.frequency),  # type: ignore[arg-type]
        min_fit=float(sub.min_fit),
        max_items=int(sub.max_items),
        email_enabled=bool(sub.email_enabled),
        last_run_at=sub.last_run_at,
    )


async def _get_or_create_subscription(session: AsyncSession, user_id: str) -> JobAlertSubscription:
    row = (
        await session.execute(
            select(JobAlertSubscription).where(JobAlertSubscription.user_id == user_id).limit(1)
        )
    ).scalar_one_or_none()
    if row is not None:
        return row
    row = JobAlertSubscription(user_id=user_id)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_job_alert_settings(session: AsyncSession, *, user_id: str) -> JobAlertSettingsResponse:
    sub = await _get_or_create_subscription(session, user_id)
    return _to_settings_response(sub)


async def patch_job_alert_settings(
    session: AsyncSession, *, user_id: str, payload: JobAlertSettingsPatch
) -> JobAlertSettingsResponse:
    sub = await _get_or_create_subscription(session, user_id)
    if payload.enabled is not None:
        sub.enabled = bool(payload.enabled)
    if payload.frequency is not None:
        sub.frequency = str(payload.frequency)
    if payload.min_fit is not None:
        sub.min_fit = float(payload.min_fit)
    if payload.max_items is not None:
        sub.max_items = int(payload.max_items)
    if payload.email_enabled is not None:
        sub.email_enabled = bool(payload.email_enabled)
    await session.commit()
    await session.refresh(sub)
    return _to_settings_response(sub)


def _render_digest_email(*, user_email: str, items: list[tuple[JobScore, Job]]) -> tuple[str, str]:
    subject = f"Doubow Job Alerts: {len(items)} new matching jobs"
    lines = [f"Hi {user_email},", "", "Here are new jobs matching your resume and preferences:", ""]
    for idx, (score, job) in enumerate(items, start=1):
        lines.append(f"{idx}. {job.title} at {job.company} ({job.location or 'n/a'}) — fit {float(score.fit_score):.1f}/5")
        reasons = [str(r).strip() for r in (score.fit_reasons or []) if str(r).strip()][:2]
        risks = [str(r).strip() for r in (score.risk_flags or []) if str(r).strip()][:1]
        for r in reasons:
            lines.append(f"   - Why match: {r}")
        for rf in risks:
            lines.append(f"   - Watchout: {rf}")
        lines.append(f"   - Link: {job.url or job.canonical_url or 'n/a'}")
        lines.append("")
    lines.extend(["- Doubow Job Alerts", ""])
    return subject, "\n".join(lines)


async def run_job_alerts_for_user(
    session: AsyncSession,
    *,
    user_id: str,
    frequency: str = "daily",
    now: datetime | None = None,
) -> dict[str, int]:
    sub = (
        await session.execute(
            select(JobAlertSubscription).where(
                JobAlertSubscription.user_id == user_id,
                JobAlertSubscription.enabled.is_(True),
                JobAlertSubscription.frequency == frequency,
            )
        )
    ).scalar_one_or_none()
    if sub is None:
        return {"candidates": 0, "sent": 0}

    user = await session.get(User, user_id)
    if user is None:
        return {"candidates": 0, "sent": 0}

    ts_now = now or datetime.now(timezone.utc)
    window = timedelta(days=7 if frequency == "weekly" else 1)
    since = sub.last_run_at or (ts_now - window)

    rows = (
        await session.execute(
            select(JobScore, Job)
            .join(Job, Job.id == JobScore.job_id)
            .outerjoin(
                JobAlertDelivery,
                and_(JobAlertDelivery.user_id == user_id, JobAlertDelivery.job_id == Job.id),
            )
            .outerjoin(
                JobDismissal,
                and_(JobDismissal.user_id == user_id, JobDismissal.job_id == Job.id),
            )
            .where(
                JobScore.user_id == user_id,
                JobScore.fit_score >= float(sub.min_fit),
                Job.discovered_at >= since,
                JobAlertDelivery.id.is_(None),
                JobDismissal.job_id.is_(None),
            )
            .order_by(JobScore.fit_score.desc(), JobScore.scored_at.desc())
            .limit(int(sub.max_items))
        )
    ).all()

    items = [(row[0], row[1]) for row in rows]
    sent = 0
    if items and sub.email_enabled:
        subject, body = _render_digest_email(user_email=user.email, items=items)
        ok = await send_email_outbound(to_addr=user.email, subject=subject, body=body)
        if ok:
            for score, _job in items:
                session.add(
                    JobAlertDelivery(
                        id=str(uuid4()),
                        user_id=user_id,
                        subscription_id=sub.id,
                        job_id=score.job_id,
                        fit_score=float(score.fit_score),
                    )
                )
            sent = len(items)
        else:
            logger.warning("job_alert send failed user_id=%s", user_id)

    sub.last_run_at = ts_now
    await session.commit()
    return {"candidates": len(items), "sent": sent}


async def run_job_alerts_for_all_users(session: AsyncSession, *, frequency: str = "daily") -> dict[str, int]:
    user_ids = (
        await session.execute(
            select(JobAlertSubscription.user_id).where(
                JobAlertSubscription.enabled.is_(True),
                JobAlertSubscription.frequency == frequency,
            )
        )
    ).scalars().all()
    total_candidates = 0
    total_sent = 0
    for uid in user_ids:
        res = await run_job_alerts_for_user(session, user_id=str(uid), frequency=frequency)
        total_candidates += int(res["candidates"])
        total_sent += int(res["sent"])
    return {"users": len(user_ids), "candidates": total_candidates, "sent": total_sent}


async def list_job_alert_feed(
    session: AsyncSession,
    *,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
) -> JobAlertFeedResponse:
    page_num = max(1, int(page))
    per_page_num = max(1, min(int(per_page), 100))
    offset = (page_num - 1) * per_page_num

    total = int(
        (
            await session.execute(
                select(func.count(JobAlertDelivery.id)).where(JobAlertDelivery.user_id == user_id)
            )
        ).scalar_one()
        or 0
    )

    rows = (
        await session.execute(
            select(JobAlertDelivery, Job, JobScore)
            .join(Job, Job.id == JobAlertDelivery.job_id)
            .outerjoin(
                JobScore,
                and_(JobScore.user_id == JobAlertDelivery.user_id, JobScore.job_id == JobAlertDelivery.job_id),
            )
            .where(JobAlertDelivery.user_id == user_id)
            .order_by(JobAlertDelivery.delivered_at.desc(), JobAlertDelivery.id.desc())
            .offset(offset)
            .limit(per_page_num)
        )
    ).all()

    items = [
        JobAlertFeedItem(
            delivery_id=str(delivery.id),
            delivered_at=delivery.delivered_at,
            fit_score=float(delivery.fit_score),
            job_id=str(job.id),
            title=str(job.title),
            company=str(job.company),
            location=job.location,
            url=job.url or job.canonical_url,
            fit_reasons=list(score.fit_reasons or []) if score else [],
            risk_flags=list(score.risk_flags or []) if score else [],
        )
        for delivery, job, score in rows
    ]
    return JobAlertFeedResponse(items=items, total=total, page=page_num, per_page=per_page_num)
