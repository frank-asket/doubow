import pytest

from models.job import Job
from models.user import User
from schemas.applications import CreateApplicationRequest
from services.applications_service import (
    ApplicationIdempotencyConflictError,
    ApplicationJobNotFoundError,
    create_application,
)


@pytest.mark.asyncio
async def test_create_application_replays_same_idempotency_key(db_session):
    db_session.add(User(id="u_app_idem", email="idem@example.com"))
    db_session.add(
        Job(
            id="job_idem_a",
            source="manual",
            external_id="ext-a",
            title="Role A",
            company="Co",
            location="Remote",
            description="d",
            url="https://example.com/a",
        )
    )
    await db_session.commit()

    payload = CreateApplicationRequest(job_id="job_idem_a", channel="email")
    key = "idem_application_create_01"

    first = await create_application(db_session, "u_app_idem", payload, idempotency_key=key)
    second = await create_application(db_session, "u_app_idem", payload, idempotency_key=key)

    assert first.id == second.id
    assert first.job.id == "job_idem_a"


@pytest.mark.asyncio
async def test_create_application_conflict_same_key_different_job(db_session):
    db_session.add(User(id="u_app_idem2", email="idem2@example.com"))
    for jid, ext in (("job_b1", "ext-b1"), ("job_b2", "ext-b2")):
        db_session.add(
            Job(
                id=jid,
                source="manual",
                external_id=ext,
                title="Role",
                company="Co",
                location="Remote",
                description="d",
                url=f"https://example.com/{jid}",
            )
        )
    await db_session.commit()

    key = "idem_application_create_02"
    await create_application(
        db_session,
        "u_app_idem2",
        CreateApplicationRequest(job_id="job_b1", channel="email"),
        idempotency_key=key,
    )

    with pytest.raises(ApplicationIdempotencyConflictError) as excinfo:
        await create_application(
            db_session,
            "u_app_idem2",
            CreateApplicationRequest(job_id="job_b2", channel="email"),
            idempotency_key=key,
        )
    assert excinfo.value.prior_application_id


@pytest.mark.asyncio
async def test_create_application_without_key_creates_distinct_rows(db_session):
    db_session.add(User(id="u_app_rand", email="rand@example.com"))
    db_session.add(
        Job(
            id="job_rand",
            source="manual",
            external_id="ext-r",
            title="Role",
            company="Co",
            location="Remote",
            description="d",
            url="https://example.com/r",
        )
    )
    await db_session.commit()

    payload = CreateApplicationRequest(job_id="job_rand", channel="email")
    a = await create_application(db_session, "u_app_rand", payload, idempotency_key=None)
    b = await create_application(db_session, "u_app_rand", payload, idempotency_key=None)
    assert a.id != b.id


@pytest.mark.asyncio
async def test_create_application_requires_existing_job(db_session):
    db_session.add(User(id="u_app_missing_job", email="missing@example.com"))
    await db_session.commit()

    with pytest.raises(ApplicationJobNotFoundError):
        await create_application(
            db_session,
            "u_app_missing_job",
            CreateApplicationRequest(job_id="job_missing", channel="email"),
            idempotency_key=None,
        )
