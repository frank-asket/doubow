# Day 18 Monitoring Drill Report

- Generated at (UTC): `2026-04-28T18:59:46Z`
- Detection latency: `N/A` (set both --incident-started-at and --alert-detected-at)

## Live Drill Fill-In

- Incident started at (UTC): `2026-04-26T21:51:21Z` (from drill event title/timestamp)
- Alert detected at (UTC): `2026-04-26T21:51:21.850596Z` (Sentry issue `firstSeen`)
- On-call owner: `UNASSIGNED (no ack record captured in available systems)`
- Detection latency result: `~0.85s`
- Threshold check (<=10m): `PASS` (timestamp-based, Sentry issue creation timing)

## Alert Routing Evidence

- Alert notification thread/link: `https://doubow.sentry.io/issues/7443338682/` (drill issue evidence)
- Dashboard link/screenshot: `https://doubow.sentry.io/issues/7443338682/`
- Incident channel summary link: `N/A (Slack/PagerDuty thread not provided)`

## Notes

- 2026-04-28 autonomous pass completed snapshot capture and evidence template wiring.
- Sentry API verification captured:
  - project alert rule exists: `Send a notification for high priority issues` (rule id `16968434`)
  - drill issue/event timestamps captured from issue `7443338682` / event `9a7a6491da804b03a693cd1271df446b`
- Remaining gap for strict operational signoff: explicit human on-call acknowledgement thread/link.

## Endpoint Snapshot

| Endpoint | Status | Latency (ms) | Key notes |
|---|---:|---:|---|
| `https://doubow-production.up.railway.app/healthz` | `200` | `603.1` | liveness check |
| `https://doubow-production.up.railway.app/ready` | `200` | `803.3` | status=ready; postgres=ok; redis=ok; background_durability={'send_mode': 'celery', 'autopilot_mode': 'celery', 'allow_inprocess_fallback_in_production': False, 'enqueue': 'ok'} |
| `https://doubow-production.up.railway.app/metrics` | `200` | `558.9` | metrics scrape surface reachable |

## Evidence Links To Add

- Alert notification screenshot/link (Slack/PagerDuty thread)
- Dashboard screenshot for 5xx/auth/readiness panel around drill window
- Incident channel summary with owner + timeline

