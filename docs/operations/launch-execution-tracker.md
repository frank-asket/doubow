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
- 2026-04-26 launch-probe (`iterations=20`) summary: `combined_5xx_rate=0.00%`, route 5xx all `0.00%`; P95 latency: jobs `616.1ms`, applications `621.1ms`, approvals `554.4ms`, agents first/full `564.6ms`; probe decision `GO`.
- Caveat: that 20-iteration run sampled `401` responses (expired/invalid token window), so reliability/latency numerics are useful baseline but do not by themselves prove authenticated-user success behavior.
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
- 2026-04-26 fresh-token one-shot auth probe after DB schema patch: `/v1/me/debug=200`, `/v1/me/applications=200`, `/v1/me/approvals=200`, `/v1/agents/chat=200` (streaming response) with `0` auth-path 5xx.

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

Manual run matrix (fill all 10):

| Run | Sign in | Resume | Discover | Pipeline | Approvals | Assistant chat | Result | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  |  |
| 9 |  |  |  |  |  |  |  |  |
| 10 |  |  |  |  |  |  |  |  |

Acceptance:

- Pass only if all 10 runs are end-to-end successful without retry hacks.
- If any run fails, record exact failing step + route + timestamp and keep gate RED.

Status: **RED**  
Evidence:

- Authenticated API blockers have been cleared by fresh-token probe (`/v1/me/*` + `/v1/agents/chat` all `200`).
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

Authenticated probe recipe (repeat 3 times to reduce token-timing noise):

```bash
export DOUBOW_LAUNCH_PROBE_TOKEN="<fresh_jwt_without_Bearer>"
LAUNCH_PROBE_ITERATIONS=10 LAUNCH_PROBE_SLEEP_SECONDS=1.0 make -C backend launch-probe
```

Evidence table (fill after each authenticated run):

| Run | Token valid at start | jobs p95 | applications p95 | approvals p95 | agents first p95 | agents full p95 | Combined 5xx | Result |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A |  |  |  |  |  |  |  |  |
| B |  |  |  |  |  |  |  |  |
| C |  |  |  |  |  |  |  |  |

Acceptance:

- Mark GREEN only when all three authenticated runs satisfy thresholds and combined/core 5xx limits.

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
- 2026-04-26 tenancy regression test: `tests/test_user_data_isolation.py` passed (`2 passed`).
- 2026-04-26 production DB check (Railway): `current_user=postgres`, `is_superuser=False`; RLS enabled on `users`, `resumes`, `jobs`, `job_scores`, `applications`, `approvals`, `chat_threads`, `chat_messages`; tenant policies present on core per-user tables.

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
- 2026-04-26 production checks: `/metrics` returns `200`; after env update and redeploy, `/ready` reports `postgres=ok` and `redis=ok`.
- 2026-04-26 runtime env check: `SENTRY_DSN` and `SENTRY_TRACES_SAMPLE_RATE` are now set on Railway `doubow`.
- 2026-04-26 Sentry ingest drill: envelope POST to `https://o4511288403034112.ingest.us.sentry.io/api/4511288475779072/envelope/` returned `200`; test event id `9a7a6491da804b03a693cd1271df446b` with tag `launch-drill-20260426-215121-9a7a6491`.
- Alert routing and drill evidence are still missing.

Owner: _(fill)_

---

## Final launch signoff

| Gate | Status | Evidence | Owner |
|---|---|---|---|
| P0-1 Core API reliability | YELLOW | Latest launch-probe (20 iterations) shows 0.00% 5xx and GO, but sample set was unauthorized (`401`) and not yet validated over a full 48-72h authenticated window | |
| P0-2 Auth/session health | GREEN | Fresh-token one-shot probe after schema repair: `/v1/me/debug`, `/v1/me/applications`, `/v1/me/approvals`, `/v1/agents/chat` all `200` with 0 auth-path 5xx | |
| P0-3 Critical journey success | RED | Authenticated API blockers are cleared in one-shot probe; gate remains red until 10/10 end-to-end manual journey runs are executed and recorded | |
| P1-4 Latency thresholds | YELLOW | P95s from 20-iteration run are within thresholds (jobs 616ms, applications 621ms, approvals 554ms, agents first/full 565ms), but measured on unauthorized (`401`) traffic, so authenticated 2xx latency evidence is still pending | |
| P1-5 Data safety/tenancy | YELLOW | Isolation tests pass and production RLS/role checks pass; remaining item is explicit support/log review for cross-user anomalies | |
| P1-6 Monitoring readiness | YELLOW | Metrics/readiness are healthy, Sentry env is configured, and ingest endpoint accepted test event (`9a7a6491da804b03a693cd1271df446b`); still need alert routing + timed drill evidence | |

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

