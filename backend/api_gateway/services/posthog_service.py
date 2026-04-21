from datetime import UTC, datetime

import httpx

from config import settings

_ACTIVATION_EVENTS = (
    "resume_upload_succeeded",
    "first_matches_ready",
)


def posthog_enabled() -> bool:
    return bool(settings.posthog_host and settings.posthog_project_api_key and settings.posthog_project_id)


async def capture_event(
    distinct_id: str,
    event_name: str,
    properties: dict | None = None,
    occurred_at: datetime | None = None,
) -> None:
    if not posthog_enabled():
        return
    payload = {
        "api_key": settings.posthog_project_api_key,
        "event": event_name,
        "distinct_id": distinct_id,
        "properties": properties or {},
        "timestamp": (occurred_at or datetime.now(UTC)).isoformat(),
    }
    url = f"{settings.posthog_host.rstrip('/')}/capture/"
    async with httpx.AsyncClient(timeout=8.0) as client:
        await client.post(url, json=payload)


async def fetch_activation_event_pairs(distinct_id: str) -> list[tuple[datetime, datetime]]:
    """Load user activation events from PostHog and pair upload->first-ready durations."""
    if not (posthog_enabled() and settings.posthog_personal_api_key):
        return []

    url = (
        f"{settings.posthog_host.rstrip('/')}/api/projects/{settings.posthog_project_id}/events/"
        f"?distinct_id={distinct_id}&limit=200"
    )
    headers = {"Authorization": f"Bearer {settings.posthog_personal_api_key}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(url, headers=headers)
        res.raise_for_status()
    data = res.json()
    results = data.get("results") or []
    events = []
    for row in results:
        name = row.get("event")
        if name not in _ACTIVATION_EVENTS:
            continue
        ts = row.get("timestamp")
        if not isinstance(ts, str):
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        events.append((name, dt))
    events.sort(key=lambda x: x[1])

    uploads: list[datetime] = []
    pairs: list[tuple[datetime, datetime]] = []
    for name, ts in events:
        if name == "resume_upload_succeeded":
            uploads.append(ts)
        elif name == "first_matches_ready" and uploads:
            start = uploads.pop(0)
            pairs.append((start, ts))
    return pairs
