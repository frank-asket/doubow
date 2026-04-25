# Launch Execution Tracker (DouBow)

Operational companion to:

- `docs/operations/launch-go-no-go-checklist.md`

Use this file to execute each gate in order and track evidence links + owner signoff.

---

## Current program status

- Date started: 2026-04-25
- Launch mode: **NO-GO** (active blocking incidents)
- Incident owner: _(fill)_
- Next review checkpoint: _(fill)_

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

- _(add probe output snippet / link)_
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

Status: **RED**  
Evidence: _(add)_

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
Evidence: _(add)_

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
Evidence: _(add)_

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
Evidence: _(add)_

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
Evidence: _(add)_

Owner: _(fill)_

---

## Final launch signoff

| Gate | Status | Evidence | Owner |
|---|---|---|---|
| P0-1 Core API reliability | RED | Pending probe + dashboard | |
| P0-2 Auth/session health | RED | Recurring production 500s | |
| P0-3 Critical journey success | RED | Blocked by API 500s | |
| P1-4 Latency thresholds | RED | Blocked by API 500s | |
| P1-5 Data safety/tenancy | YELLOW | Needs prod-role validation | |
| P1-6 Monitoring readiness | YELLOW | Needs alert drill proof | |

Decision: **NO-GO** (until all P0 green and P1 green)

