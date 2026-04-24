"""Application-layer tenancy: authenticated user id always scopes queries (RLS complement).

Postgres RLS with a non-superuser role must still be validated in staging; these tests prove
service/router contracts filter by ``user_id``. See ``docs/operations/slo-and-incidents.md``.
"""

import pytest

from models.application import Application
from models.job import Job
from models.user import User
from services.applications_service import list_applications
from services.prep_service import generate_prep_for_application, get_prep_detail_for_user


@pytest.mark.asyncio
async def test_list_applications_excludes_other_users_apps(db_session):
    ua, ub = "user_iso_a", "user_iso_b"
    db_session.add(User(id=ua, email="a@example.com"))
    db_session.add(User(id=ub, email="b@example.com"))
    jid = "job_iso_1"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="iso-j",
            title="Engineer",
            company="Co",
            location="Remote",
            description="Desc",
            url="https://example.com/j",
        )
    )
    await db_session.commit()

    app_a = "app_iso_a"
    app_b = "app_iso_b"
    db_session.add(Application(id=app_a, user_id=ua, job_id=jid, status="pending", channel="email"))
    db_session.add(Application(id=app_b, user_id=ub, job_id=jid, status="pending", channel="email"))
    await db_session.commit()

    res_a = await list_applications(db_session, ua, None)
    ids_a = {x.id for x in res_a.items}
    assert app_a in ids_a
    assert app_b not in ids_a

    res_b = await list_applications(db_session, ub, None)
    ids_b = {x.id for x in res_b.items}
    assert app_b in ids_b
    assert app_a not in ids_b


@pytest.mark.asyncio
async def test_prep_detail_not_visible_to_other_user(db_session):
    ua, ub = "user_prep_iso_a", "user_prep_iso_b"
    db_session.add(User(id=ua, email="pa@example.com"))
    db_session.add(User(id=ub, email="pb@example.com"))
    jid = "job_prep_iso"
    db_session.add(
        Job(
            id=jid,
            source="manual",
            external_id="prep-j",
            title="PM",
            company="Stripe",
            location="Remote",
            description="Build",
            url="https://example.com/job",
        )
    )
    await db_session.commit()

    app_b = "app_prep_iso_b"
    db_session.add(Application(id=app_b, user_id=ub, job_id=jid, status="pending", channel="email"))
    await db_session.commit()

    await generate_prep_for_application(db_session, ub, app_b)

    assert await get_prep_detail_for_user(db_session, ub, app_b) is not None
    assert await get_prep_detail_for_user(db_session, ua, app_b) is None
