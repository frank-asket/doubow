# Week 3 Execution Plan (Post-Day-14 Launch Closure)

Date window: 2026-04-29 to 2026-05-05  
Objective: turn remaining RED launch gates to GREEN and move from NO-GO to GO readiness.

---

## Week 3 Outcomes

- Production background durability runs in Celery mode for send + autopilot, with healthy enqueue.
- Core reliability and latency evidence captured on authenticated traffic.
- Monitoring readiness closed with alert-route drill evidence.
- OAuth reconnect hardening signoff complete for in-scope providers.
- Final launch scorecard updated with owner signoff.

---

## Day 15 - Durable Background Mode Cutover

- Apply Railway env values:
  - `USE_CELERY_FOR_SEND=true`
  - `USE_CELERY_FOR_AUTOPILOT=true`
  - `ALLOW_INPROCESS_BACKGROUND_IN_PRODUCTION=false`
- Confirm worker deployment and queue consumption.
- Redeploy backend + workers.
- Validate `/ready.background_durability` returns celery/celery + enqueue ok.

Definition of done:

- `/ready` evidence attached showing `send_mode=celery`, `autopilot_mode=celery`, `enqueue=ok`.
- No deployment regressions in `/healthz` or `/metrics`.

Current note (2026-04-28):

- Initial CLI attempt showed in-process runtime mode and required dashboard-level verification.
- Final verification passed: `/ready` now returns `send_mode=celery`, `autopilot_mode=celery`, `allow_inprocess_fallback_in_production=false`, `enqueue=ok`.
- Day 15 outcome: durable background cutover complete.

---

## Day 16 - Authenticated Reliability Evidence (P0-1)

- Run authenticated `auth-probe` and `launch-probe` with fresh token.
- Capture probe outputs and route-level 5xx summary.
- Correlate with Railway + Sentry for repeated 5xx patterns.

Definition of done:

- P0-1 can be marked GREEN with authenticated evidence, or blocker ticket opened with exact failing route, timestamp, and owner.

---

## Day 17 - Authenticated Latency Evidence (P1-4)

- Run three authenticated latency samples (A/B/C) using tracker recipe.
- Fill latency evidence table in `launch-execution-tracker.md`.
- Compare against p95 thresholds for all core routes.

Definition of done:

- P1-4 marked GREEN, or explicit threshold breach logged with remediation owner/date.

---

## Day 18 - Monitoring Drill and Alert Routing (P1-6)

- Verify alert routes for 5xx spike, auth-path errors, and readiness degradation.
- Execute one timed incident drill and capture detection latency.
- Link evidence (channel/thread/screenshot + timestamp) in tracker.

Definition of done:

- P1-6 marked GREEN with <=10 min detection in test drill and named on-call owner.

---

## Day 19 - Data Safety Ops Review (P1-5)

- Review support/log channels for cross-tenant anomaly signals.
- Confirm no mixed-user records or leakage complaints.
- Record review window and reviewer identity in tracker.

Definition of done:

- P1-5 marked GREEN with explicit ops review evidence and reviewer signoff.

---

## Day 20 - OAuth Hardening Signoff (Step 7)

- Execute reconnect runbook on production for in-scope provider(s).
- Capture status/authorize preflight and functional reconnect verification.
- Record secret rotation/signoff details.

Definition of done:

- Step 7 marked GREEN, or explicit in/out-of-scope provider policy documented with risk owner signoff.

---

## Day 21 - Final Launch Board and Decision Review

- Reconcile gate statuses in:
  - `docs/operations/launch-execution-tracker.md`
  - `docs/operations/launch-go-no-go-checklist.md`
- Fill owners and final decision fields.
- Produce short decision memo for launch review.

Definition of done:

- Single-source gate board is internally consistent and ready for launch committee decision.

