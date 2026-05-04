"""Scrapling seed URL resolution (explicit + Greenhouse boards from Doubow config)."""

import pytest

from config import settings
from services.scrapling_adapter import effective_scrapling_seed_urls


def test_effective_seeds_explicit_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "scrapling_seed_urls", "https://a.test/j1,https://a.test/j2")
    monkeypatch.setattr(settings, "scrapling_auto_greenhouse_board_seeds", True)
    monkeypatch.setattr(settings, "greenhouse_board_tokens", None)
    out = effective_scrapling_seed_urls(settings)
    assert out == ["https://a.test/j1", "https://a.test/j2"]


def test_effective_seeds_merges_greenhouse_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "scrapling_seed_urls", "https://manual.test/1")
    monkeypatch.setattr(settings, "scrapling_auto_greenhouse_board_seeds", True)
    monkeypatch.setattr(settings, "greenhouse_board_tokens", "acme")
    monkeypatch.setattr(settings, "greenhouse_api_url", "https://boards-api.greenhouse.io/v1/boards")
    monkeypatch.setattr(settings, "scrapling_greenhouse_seed_jobs_per_board", 3)
    monkeypatch.setattr(settings, "scrapling_timeout_s", 30.0)

    def fake_fetch(_cfg) -> list[str]:  # noqa: ANN001
        return [
            "https://job-boards.greenhouse.io/acme/jobs/1",
            "https://job-boards.greenhouse.io/acme/jobs/2",
        ]

    monkeypatch.setattr(
        "services.scrapling_adapter._fetch_greenhouse_job_detail_urls_for_scrapling",
        fake_fetch,
    )
    out = effective_scrapling_seed_urls(settings)
    assert out[0] == "https://manual.test/1"
    assert "https://job-boards.greenhouse.io/acme/jobs/1" in out
    assert "https://job-boards.greenhouse.io/acme/jobs/2" in out


def test_effective_seeds_dedupes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "scrapling_seed_urls", "https://shared.test/job")
    monkeypatch.setattr(settings, "scrapling_auto_greenhouse_board_seeds", True)
    monkeypatch.setattr(settings, "greenhouse_board_tokens", "x")

    def fake_fetch(_cfg) -> list[str]:  # noqa: ANN001
        return ["https://shared.test/job", "https://other.test/job"]

    monkeypatch.setattr(
        "services.scrapling_adapter._fetch_greenhouse_job_detail_urls_for_scrapling",
        fake_fetch,
    )
    out = effective_scrapling_seed_urls(settings)
    assert out == ["https://shared.test/job", "https://other.test/job"]
