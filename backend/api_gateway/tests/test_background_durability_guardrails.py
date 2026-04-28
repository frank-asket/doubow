import sys
import types

from schemas.approvals import ApproveApprovalResponse
from schemas.autopilot import AutopilotRunResponse
from config import settings


def test_effective_celery_defaults_follow_environment(monkeypatch):
    monkeypatch.setattr(settings, "use_celery_for_send", None)
    monkeypatch.setattr(settings, "use_celery_for_autopilot", None)

    monkeypatch.setattr(settings, "environment", "production")
    assert settings.use_celery_for_send_effective() is True
    assert settings.use_celery_for_autopilot_effective() is True

    monkeypatch.setattr(settings, "environment", "development")
    assert settings.use_celery_for_send_effective() is False
    assert settings.use_celery_for_autopilot_effective() is False


def test_approvals_returns_503_when_celery_enqueue_fails_in_production(client, monkeypatch):
    import routers.approvals as approvals_router

    class _FailingTask:
        @staticmethod
        def delay(*_args, **_kwargs):
            raise RuntimeError("broker unavailable")

    async def _approve_ok(*_args, **_kwargs):
        return ApproveApprovalResponse(
            approval_id="appr_1",
            status="approved",
            queued_send=True,
            send_task_id="stub_task_1",
        )

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allow_inprocess_background_in_production", False)
    monkeypatch.setattr(settings, "use_celery_for_send", True)
    monkeypatch.setattr(approvals_router, "approve_approval_service", _approve_ok)
    monkeypatch.setitem(
        sys.modules,
        "tasks.send_tasks",
        types.SimpleNamespace(send_approval_stub_task=_FailingTask()),
    )

    res = client.post(
        "/v1/me/approvals/appr_1/approve",
        headers={"Idempotency-Key": "abcdefgh"},
        json={"edited_body": "approved text"},
    )
    assert res.status_code == 503
    assert "durable worker enqueue failed" in res.json()["detail"]


def test_approvals_fallback_allowed_when_escape_hatch_enabled(client, monkeypatch):
    import routers.approvals as approvals_router

    class _FailingTask:
        @staticmethod
        def delay(*_args, **_kwargs):
            raise RuntimeError("broker unavailable")

    async def _approve_ok(*_args, **_kwargs):
        return ApproveApprovalResponse(
            approval_id="appr_2",
            status="approved",
            queued_send=True,
            send_task_id="stub_task_2",
        )

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allow_inprocess_background_in_production", True)
    monkeypatch.setattr(settings, "use_celery_for_send", True)
    monkeypatch.setattr(approvals_router, "approve_approval_service", _approve_ok)
    monkeypatch.setitem(
        sys.modules,
        "tasks.send_tasks",
        types.SimpleNamespace(send_approval_stub_task=_FailingTask()),
    )

    res = client.post(
        "/v1/me/approvals/appr_2/approve",
        headers={"Idempotency-Key": "abcdefgh"},
        json={"edited_body": "approved text"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["approval_id"] == "appr_2"
    assert body["queued_send"] is True


def test_autopilot_returns_503_when_celery_enqueue_fails_in_production(client, monkeypatch):
    import routers.autopilot as autopilot_router

    class _FailingTask:
        @staticmethod
        def delay(*_args, **_kwargs):
            raise RuntimeError("broker unavailable")

    async def _run_ok(*_args, **_kwargs):
        return (
            AutopilotRunResponse(run_id="run_1", status="queued", scope="all"),
            False,
        )

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allow_inprocess_background_in_production", False)
    monkeypatch.setattr(settings, "use_celery_for_autopilot", True)
    monkeypatch.setattr(autopilot_router, "run_autopilot_service", _run_ok)
    monkeypatch.setitem(
        sys.modules,
        "tasks.autopilot_tasks",
        types.SimpleNamespace(autopilot_run_task=_FailingTask()),
    )

    res = client.post(
        "/v1/me/autopilot/run",
        headers={"Idempotency-Key": "abcdefgh"},
        json={"scope": "all"},
    )
    assert res.status_code == 503
    assert "durable worker enqueue failed" in res.json()["detail"]

