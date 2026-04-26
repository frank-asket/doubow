# Launch Execution Tracker (DouBow)

Operational companion to:

- `docs/operations/launch-go-no-go-checklist.md`

Use this file to execute each gate in order and track evidence links + owner signoff.

---

## Current program status

- Date started: 2026-04-25
- Launch mode: **NO-GO** (active blocking incidents)
- Incident owner: _(fill)_
- Next review checkpoint: **Immediately after next Railway backend deploy + fresh-token probe rerun**

---

## Step-by-step execution

### Step 1 — P0-1 Core API reliability

Goal:

- 5xx per critical route <= 0.5%
- Combined 5xx <= 0.25%
- No sustained burst > 5 min

Execution:

1. Run probe script with a real Clerk user token:

```bash
export DOUBOW_LAUNCH_PROBE_TOKEN="<clerk_jwt>"
python3 scripts/launch_gate_probe.py \
  --base-url https://doubow-production.up.railway.app \
  --iterations 20 \
  --sleep-seconds 2 \
  --token-env DOUBOW_LAUNCH_PROBE_TOKEN
```

Or via Make target:

```bash
export DOUBOW_LAUNCH_PROBE_TOKEN="<clerk_jwt>"
make -C backend launch-probe
```

2. Capture route-level metrics dashboard screenshot/query.
3. Confirm no repeating 500s in Railway + Sentry.

Status: **RED**  
Evidence:

- 2026-04-25 point-in-time probe with valid auth (short-lived Clerk token): `/v1/me/applications`, `/v1/me/approvals`, `POST /v1/agents/chat` returned `500`; `/v1/me/debug` returned `200`.
- 2026-04-25 probe resilience hardening shipped in scripts: network failures now record `599` in both `scripts/auth_gate_probe.py` and `scripts/launch_gate_probe.py` instead of crashing.
- 2026-04-26 probe (valid token at request time): `/v1/me/debug=200`, `/v1/me/applications=500`, `/v1/me/approvals=503`, `/v1/agents/chat=200` with SSE fallback error payload.
- 2026-04-26 readiness check: `/ready` returned `postgres=ok`, `redis=degraded` with `localhost:6379 connection refused` (production Redis env not healthy).
- _(add dashboard link)_

Owner: _(fill)_

---

### Step 2 — P0-2 Auth/session health

Goal:

- No recurring auth-path 5xx (`get_authenticated_user`, token verification, user-upsert)
- No JWKS fetch regressions

Execution:

1. Inspect logs for:
   - `Auth user upsert failed`
   - `Authentication provider temporarily unavailable`
2. Validate Clerk deployment settings (issuer/audience) match production.
3. Run authenticated request checks:
   - `GET /v1/me/applications`
   - `GET /v1/me/approvals`
   - `POST /v1/agents/chat`

Probe command:

```bash
export DOUBOW_LAUNCH_PROBE_TOKEN="<clerk_jwt>"
make -C backend auth-probe
```

Status: **RED**  
Evidence:

- 2026-04-25: multiple probe runs with expired Clerk session JWTs returned `401 Invalid auth token` consistently (expected for expired tokens; not sufficient to clear gate).
- 2026-04-25: run with token still valid at probe start (`exp_in_s > 0`) showed `/v1/me/debug=200` while `/v1/me/applications`, `/v1/me/approvals`, `POST /v1/agents/chat` returned `500`, confirming backend failures on authenticated path.
- Pending deploy fix: `/v1/me/debug` now uses `get_authenticated_user` (same dependency path as other `/v1/me/*` routes) to avoid false-green auth checks.
- Pending deploy fix: `services/job_score_mapping.py` now coerces `fit_reasons` / `risk_flags` to `list[str]` to prevent response-model validation 500s on malformed score payloads.
- 2026-04-26 runtime behavior indicates partial deploy of guards (approvals/chat degraded gracefully) but not full elimination of applications failures; requires latest full backend deploy + logs verification.

Owner: _(fill)_

---

### Step 3 — P0-3 Critical journey success

Goal:

- 10/10 manual runs successful:
  sign-in -> resume -> discover -> pipeline -> approvals -> assistant chat

Execution:

1. Run manual checklist with fresh browser session.
2. Record each run result (success/failure + failing step).
3. Attach video/GIF for at least one successful full run.

Status: **RED**  
Evidence:

- Blocked by unresolved authenticated-route 500s in Step 1/2.
- Next execution immediately after backend deploy:
  - run 10 manual journeys end-to-end (fresh session each run),
  - record per-step pass/fail,
  - attach one full successful run capture.

Owner: _(fill)_

---

### Step 4 — P1-4 Latency thresholds

Goal:

- P95 latency thresholds from launch checklist all green.

Execution:

1. Use probe output + observability dashboards.
2. Validate:
   - `/v1/jobs` <= 1500ms P95
   - `/v1/me/applications` <= 1000ms P95
   - `/v1/me/approvals` <= 1000ms P95
   - `/v1/agents/chat` first payload <= 3000ms, full typical <= 15000ms

Status: **RED**  
Evidence:

- Current latency numbers were measured mostly under `401` or failing `500` responses; not valid for launch signoff.
- Re-run latency gate only after Step 1/2 produce stable authenticated `2xx` responses.

Owner: _(fill)_

---

### Step 5 — P1-5 Data safety and tenancy

Goal:

- No cross-tenant leakage risk.

Execution:

1. Run backend isolation tests (or CI equivalent) and save result.
2. Validate production DB role + RLS behavior in staging/prod-like env.
3. Review support/logs for mixed-user data anomalies.

Status: **YELLOW**  
Evidence:

- Service-level data-shape guards implemented for jobs/applications/approvals mapping (malformed rows skipped and logged).
- Pending production verification of RLS + DB role behavior with non-superuser credentials.

Owner: _(fill)_

---

### Step 6 — P1-6 Monitoring and incident readiness

Goal:

- Sentry + alerts + dashboards fully wired and owned.

Execution:

1. Confirm Sentry receives backend exceptions.
2. Confirm alerts for 5xx/auth/readiness fire to on-call channel.
3. Perform one alert drill and capture time-to-detect.

Status: **YELLOW**  
Evidence:

- `/metrics` endpoint exists and route-level metrics middleware is active.
- Pending confirmation that alerts route to on-call and alert drill is completed.

Owner: _(fill)_

---

## Final launch signoff

| Gate | Status | Evidence | Owner |
|---|---|---|---|
| P0-1 Core API reliability | RED | 2026-04-25 valid-token probe: 500 on applications/approvals/agents_chat | |
| P0-2 Auth/session health | RED | Auth verifies, but authenticated route path still emits 500s | |
| P0-3 Critical journey success | RED | Blocked by unresolved authenticated-route failures | |
| P1-4 Latency thresholds | RED | Must rerun on stable authenticated 2xx traffic | |
| P1-5 Data safety/tenancy | YELLOW | Needs prod-role validation | |
| P1-6 Monitoring readiness | YELLOW | Needs alert drill proof | |

Decision: **NO-GO** (until all P0 green and P1 green)

---

## Execution Completion Checklist (Operator)

These are the remaining live-environment steps required to complete this tracker.

1. Deploy current backend to Railway (latest `main`).
2. Confirm Railway env:
   - `DATABASE_URL` points to production Postgres.
   - `REDIS_URL` is set to real Redis (not localhost).
   - Clerk issuer/audience values match production token issuer.
3. Run probe rerun with a fresh JWT (within token lifetime):

```bash
export DOUBOW_LAUNCH_PROBE_TOKEN="<fresh_jwt_without_Bearer>"
AUTH_PROBE_ITERATIONS=1 AUTH_PROBE_SLEEP_SECONDS=0 make -C backend auth-probe
LAUNCH_PROBE_ITERATIONS=20 LAUNCH_PROBE_SLEEP_SECONDS=2 make -C backend launch-probe
```

4. Attach evidence to this file:
   - probe summaries,
   - `/ready` output,
   - Railway logs around failing routes (if any),
   - dashboard screenshots/queries for 5xx + latency.
5. If any route still fails, patch and redeploy, then repeat steps 3-4 until all P0 gates are green.

