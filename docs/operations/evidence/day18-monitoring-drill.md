# Day 18 Monitoring Drill Report

- Generated at (UTC): `2026-04-28T18:59:46Z`
- Detection latency: `N/A` (set both --incident-started-at and --alert-detected-at)

## Live Drill Fill-In

- Incident started at (UTC): `N/A (external alert trigger not executed from this workspace)`
- Alert detected at (UTC): `N/A (requires Slack/PagerDuty visibility)`
- On-call owner: `UNASSIGNED`
- Detection latency result: `N/A`
- Threshold check (<=10m): `BLOCKED`

## Alert Routing Evidence

- Alert notification thread/link: `N/A (not accessible from current workspace tools)`
- Dashboard link/screenshot: `Pending operator attachment`
- Incident channel summary link: `N/A (not accessible from current workspace tools)`

## Notes

- 2026-04-28 autonomous pass completed snapshot capture and evidence template wiring.
- Final Day 18 GREEN signoff remains blocked on external alert-routing proof and timed drill timestamps from on-call systems.

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

