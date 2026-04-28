# Day 14 Release Gate + Handoff (DouBow)

Date: 2026-04-28  
Scope: Week 2 Day 14 closeout (release gate decision + operator handoff)

---

## Executive Decision

- **Launch decision:** **NO-GO** for broad/public launch.
- **Why:** Not all P0/P1 gates are green yet, and OAuth reconnect hardening is still open in production signoff.
- **What is still safe today:** Controlled internal/beta usage with active operator monitoring.

---

## Production Background Mode Decision (Explicit)

- **Decision:** Public launch requires **Celery-backed durable mode** for both send and autopilot paths.
- **Current observed state (2026-04-28):**
  - `/ready.background_durability.send_mode = "inprocess"`
  - `/ready.background_durability.autopilot_mode = "inprocess"`
  - `allow_inprocess_fallback_in_production = false`
- **Gate outcome from this mismatch:** **NO-GO** until durable mode is restored and verified in production.

Rationale:

- In-process background execution is acceptable as a temporary continuity mode.
- It is not the intended production durability posture for launch traffic because queue/worker decoupling and replay guarantees are weaker under failure/restart pressure.

---

## Required Actions Before GO

1. Set production env to durable defaults:
   - `USE_CELERY_FOR_SEND=true`
   - `USE_CELERY_FOR_AUTOPILOT=true`
   - `ALLOW_INPROCESS_BACKGROUND_IN_PRODUCTION=false`
2. Ensure Celery workers are running and consuming expected queues.
3. Redeploy backend + workers.
4. Verify readiness reports durable mode:
   - `background_durability.send_mode == "celery"`
   - `background_durability.autopilot_mode == "celery"`
   - `background_durability.enqueue == "ok"`
5. Run authenticated probe reruns and attach evidence for Step 1/4 thresholds.
6. Complete OAuth Step 7 signoff evidence (Google reconnect minimum; LinkedIn optional only if explicitly out of scope).
7. Complete monitoring drill evidence (alert route + time-to-detect <= 10 min).

---

## Operator Runbook Snippets

Readiness check:

```bash
curl -sS https://doubow-production.up.railway.app/ready | python3 -m json.tool
```

Authenticated probe rerun:

```bash
export DOUBOW_LAUNCH_PROBE_TOKEN="<fresh_jwt_without_Bearer>"
AUTH_PROBE_ITERATIONS=1 AUTH_PROBE_SLEEP_SECONDS=0 make -C backend auth-probe
LAUNCH_PROBE_ITERATIONS=20 LAUNCH_PROBE_SLEEP_SECONDS=2 make -C backend launch-probe
```

---

## Handoff Ownership

- **Incident/launch owner:** fill in `docs/operations/launch-execution-tracker.md`.
- **Backend durability owner:** platform/backend on-call.
- **Auth/OAuth owner:** integrations owner.
- **Monitoring drill owner:** SRE/on-call lead.

---

## Exit Criteria to Flip NO-GO -> GO

- All P0 gates = **GREEN**.
- All P1 gates = **GREEN**.
- OAuth reconnect hardening Step 7 = **GREEN** (or explicitly deferred with written scope and risk signoff).
- Production readiness confirms Celery durable background mode with healthy enqueue.
