# Launch Go/No-Go Checklist (DouBow)

Use this as the final gate before any paid acquisition or broad user onboarding.

Telemetry reference for launch funnel instrumentation:
- `docs/operations/funnel-event-map.md`

---

## Decision rule

- **GO** only if **all P0 and P1 gates pass** for the full observation window.
- **NO-GO** if any P0 gate fails at any time, or if any P1 gate is red at decision time.

Recommended observation window:

- **Minimum:** 48 hours
- **Preferred:** 72 hours

---

## P0 Gates (must pass)

### 1) Core API reliability

Scope (authenticated, production traffic):

- `GET /v1/jobs`
- `GET /v1/me/applications`
- `GET /v1/me/approvals`
- `POST /v1/agents/chat`

Thresholds:

- 5xx rate per route: **<= 0.5%** over rolling 1 hour
- 5xx rate combined (4 routes): **<= 0.25%** over rolling 1 hour
- No sustained 5xx burst > **5 minutes**

Fail condition:

- Any route exceeds threshold in two consecutive 1h windows, or any outage > 5 min.

---

### 2) Authentication and session health (Clerk + API)

Thresholds:

- 401s due to expected unauthenticated traffic are allowed.
- 5xx from auth dependency path (`get_authenticated_user`, token verification, user upsert): **0 recurring incidents** in window.
- Clerk/JWKS fetch failures causing user-facing failures: **0**.

Fail condition:

- Any auth-path exception pattern repeats after hotfix/redeploy.

---

### 3) End-to-end critical user journey

Journey:

1. Sign in
2. Upload/view resume
3. Discover jobs
4. View pipeline/applications
5. Open approvals
6. Send assistant message

Thresholds:

- Manual smoke runs: **10/10 successful** (no refresh/retry hacks)
- Synthetic smoke job (if available): **>= 99% success**

Fail condition:

- Any hard blocker in journey (500, stuck loading, auth loop).

---

## P1 Gates (must pass)

### 4) Latency and UX responsiveness

Thresholds (P95, production):

- `GET /v1/jobs`: **<= 1500 ms**
- `GET /v1/me/applications`: **<= 1000 ms**
- `GET /v1/me/approvals`: **<= 1000 ms**
- `POST /v1/agents/chat`:
  - first token / first SSE payload <= **3000 ms**
  - full response (typical) <= **15000 ms**

Fail condition:

- Any route above threshold in two consecutive windows.

---

### 5) Data safety and tenancy

Checks:

- No cross-tenant leakage in logs, support reports, or tests.
- RLS + app DB role validated under production-like permissions.
- Idempotency behavior confirmed for approvals/chat flows where applicable.

Thresholds:

- Critical data isolation incidents: **0**

Fail condition:

- Any PII or cross-user data leak risk.

---

### 6) Monitoring and incident readiness

Required:

- Sentry enabled and receiving backend exceptions.
- Route-level dashboard for 5xx and latency.
- Alerting configured for:
  - 5xx spike
  - auth-path failures
  - readiness degradation

Threshold:

- Mean time to identify incident from alert: **<= 10 min** in test drill.

Fail condition:

- No reliable alert path or no on-call owner.

---

## Launch scorecard (fill at decision time)

| Gate | Status (Green/Red) | Evidence link | Owner |
|---|---|---|---|
| P0-1 Core API reliability | Red | `docs/operations/launch-execution-tracker.md` (Step 1: authenticated window evidence still incomplete) | _(fill)_ |
| P0-2 Auth/session health | Green | `docs/operations/launch-execution-tracker.md` (Step 2: fresh-token probe all 200) | _(fill)_ |
| P0-3 Critical journey success | Green | `docs/operations/launch-execution-tracker.md` + `docs/operations/evidence/day12-cold-run/` (strict cold runs 8-10 pass) | _(fill)_ |
| P1-4 Latency thresholds | Red | `docs/operations/launch-execution-tracker.md` (needs authenticated 2xx p95 reruns A/B/C) | _(fill)_ |
| P1-5 Data safety/tenancy | Red | `docs/operations/launch-execution-tracker.md` (support-log anomaly review pending) | _(fill)_ |
| P1-6 Monitoring readiness | Red | `docs/operations/launch-execution-tracker.md` (alert routing + timed drill pending) | _(fill)_ |

Final decision:

- **GO / NO-GO:** **NO-GO**
- Date/time: **2026-04-28**
- Incident commander: _(fill)_
- Notes:
  - Public launch blocked pending remaining red gates.
  - Explicit Day 14 production decision: require Celery durable background mode for launch; current production `/ready` reports `inprocess` for send/autopilot.
  - Reference handoff: `docs/operations/day14-release-gate-handoff.md`.

---

## Immediate NO-GO triggers (override)

Even if scorecard is mostly green, force **NO-GO** on:

- Any unresolved repeating 500 on core routes
- Any auth loop/session corruption pattern
- Any data isolation concern
- Any unresolved payment/approval-send correctness risk

---

## Post-GO guardrails (first 7 days)

- Keep daily check-in on:
  - 5xx rate for core routes
  - funnel completion (signin -> discover -> pipeline)
  - support tickets tagged `auth`, `500`, `data-mismatch`
- Pause ads automatically if:
  - combined core-route 5xx > **1.0%** for > 30 min
  - critical journey completion drops below **90%** for > 1h

