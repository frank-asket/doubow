# Day 18 Monitoring Drill Runbook

Goal: close Week 3 Day 18 (P1-6) with verifiable alert-routing and incident-detection evidence.

## What this run proves

- Alert route exists and reaches the on-call channel.
- On-call owner is explicitly identified.
- Detection latency (incident start -> first alert observed) is <= 10 minutes.

## Inputs to collect during the drill

- `incident_started_at` (UTC ISO8601), when the synthetic incident starts.
- `alert_detected_at` (UTC ISO8601), when first alert lands in Slack/PagerDuty.
- On-call owner handle/name.
- Alert thread link or screenshot.
- Dashboard screenshot covering 5xx/auth/readiness around the same time window.

## 1) Run the evidence snapshot script

From repo root:

```bash
DRILL_INCIDENT_STARTED_AT="2026-04-28T19:10:00Z" \
DRILL_ALERT_DETECTED_AT="2026-04-28T19:14:25Z" \
DRILL_ONCALL_OWNER="@oncall-engineering" \
make -C backend monitoring-drill-report
```

Default output:

- `docs/operations/evidence/day18-monitoring-drill.md`

Optional custom output:

```bash
DRILL_REPORT_OUTPUT="docs/operations/evidence/day18-monitoring-drill-$(date +%Y%m%d-%H%M%S).md" \
make -C backend monitoring-drill-report
```

## 2) Attach external evidence links

Edit the generated markdown and paste:

- Alert message thread URL (or screenshot path)
- Incident timeline thread URL
- Dashboard screenshot URL/path

## 3) Update launch tracker

In `docs/operations/launch-execution-tracker.md` Step 6:

- Set status to `GREEN` only when:
  - report shows detection latency <= 600 seconds
  - alert-routing evidence is linked
  - on-call owner is named

## Notes

- This script does not trigger incidents itself; it standardizes evidence capture from a real drill.
- Keep all timestamps in UTC.
