"""Resume-aligned filtering on legacy ingestion connectors."""

from datetime import datetime, timezone

from ingestion.connectors.base import BaseConnector, JobRecord, RawJob
from services.provider_adapter import ProviderFetchParams


class _StubConnector(BaseConnector):
    source_name = "stub"

    async def fetch(self):  # pragma: no cover - overridden in test
        yield RawJob(
            source="stub",
            external_id="1",
            title="Senior Python Engineer",
            company="Acme",
            url="https://example.com/j/1",
            description="x" * 50,
            location="Berlin",
        )


def test_matches_resume_query_requires_keyword_token() -> None:
    c = _StubConnector()
    c.set_fetch_context(ProviderFetchParams(keywords="golang rust", location=None, page=1, per_page=20))
    rec = JobRecord(
        id="i",
        source="stub",
        external_id="1",
        dedup_hash="h",
        title="Python developer",
        company="Co",
        url="https://u",
        description="y" * 50,
        location="Remote",
        remote=True,
        salary_range="",
        salary_min=None,
        salary_max=None,
        currency="USD",
        posted_at=None,
        discovered_at=datetime.now(timezone.utc),
        tags=[],
        department="",
        employment_type="full_time",
    )
    assert c._matches_resume_query(rec) is False

    c.set_fetch_context(ProviderFetchParams(keywords="python django", location=None, page=1, per_page=20))
    assert c._matches_resume_query(rec) is True
