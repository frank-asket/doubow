from services.approvals_service import ApprovalIdempotencyConflictError


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
