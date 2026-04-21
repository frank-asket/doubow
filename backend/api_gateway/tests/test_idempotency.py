from services.applications_service import ApplicationIdempotencyConflictError
from services.approvals_service import ApprovalIdempotencyConflictError


def test_application_create_idempotency_conflict_envelope(client, monkeypatch):
    async def _raise_conflict(**kwargs):
        raise ApplicationIdempotencyConflictError("app_prev_001")

    monkeypatch.setattr("routers.applications.create_application", _raise_conflict)

    res = client.post(
        "/v1/me/applications",
        json={"job_id": "j1", "channel": "email"},
        headers={"Idempotency-Key": "idem-app-create-12345"},
    )

    assert res.status_code == 409
    assert res.json() == {
        "error": "idempotency_conflict",
        "detail": "Key already used for a different application payload",
        "prior_application_id": "app_prev_001",
    }


def test_application_create_not_found_envelope(client, monkeypatch):
    async def _raise_not_found(**kwargs):
        from services.applications_service import ApplicationJobNotFoundError

        raise ApplicationJobNotFoundError("Job not found: j404")

    monkeypatch.setattr("routers.applications.create_application", _raise_not_found)

    res = client.post(
        "/v1/me/applications",
        json={"job_id": "j404", "channel": "email"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Job not found: j404"


def test_autopilot_idempotency_conflict_envelope(client, monkeypatch):
    async def _raise_conflict(**kwargs):
        raise ValueError("run_prev_001")

    monkeypatch.setattr("routers.autopilot.run_autopilot_service", _raise_conflict)

    res = client.post(
        "/v1/me/autopilot/run",
        json={"scope": "all", "application_ids": ["a_1"]},
        headers={"Idempotency-Key": "idem-key-12345"},
    )

    assert res.status_code == 409
    assert res.json() == {
        "error": "idempotency_conflict",
        "detail": "Key already used with a different payload fingerprint",
        "prior_run_id": "run_prev_001",
    }


def test_approval_idempotency_conflict_envelope(client, monkeypatch):
    async def _raise_conflict(**kwargs):
        raise ApprovalIdempotencyConflictError("ap_prev_001")

    monkeypatch.setattr("routers.approvals.approve_approval_service", _raise_conflict)

    res = client.post(
        "/v1/me/approvals/ap_001/approve",
        json={"edited_body": "updated text"},
        headers={"Idempotency-Key": "idem-key-67890"},
    )

    assert res.status_code == 409
    assert res.json() == {
        "error": "idempotency_conflict",
        "detail": "Key already used with a different approval submission",
        "prior_approval_id": "ap_prev_001",
    }


def test_reject_approval_not_found_returns_404(client, monkeypatch):
    async def _raise_not_found(**kwargs):
        raise ValueError("Approval not found")

    monkeypatch.setattr("routers.approvals.reject_approval_service", _raise_not_found)

    res = client.post("/v1/me/approvals/ap_missing/reject")
    assert res.status_code == 404
    assert res.json() == {"detail": "Approval not found"}


def test_dismiss_job_not_found_returns_404(client, monkeypatch):
    async def _raise_not_found(**kwargs):
        raise LookupError("job_not_found")

    monkeypatch.setattr("routers.jobs.dismiss_job_for_user", _raise_not_found)

    res = client.post("/v1/jobs/job_missing/dismiss")
    assert res.status_code == 404
    assert res.json() == {"detail": "Job not found"}
