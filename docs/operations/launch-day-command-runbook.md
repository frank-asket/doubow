# Launch Day Command Runbook (Day 10)

Purpose: one-page operator runbook for final launch-day verification and GO/NO-GO decision.

Related docs:
- `docs/operations/launch-execution-tracker.md`
- `docs/operations/launch-go-no-go-checklist.md`
- `docs/operations/funnel-event-map.md`
- `docs/operations/oauth-hardening-reconnect-runbook.md`
- `docs/operations/checkout-e2e-20min.md`
- `docs/operations/launch-day-execution-checklist.md` (checkbox-only)

---

## Roles

- **Release manager:** runs ceremony, records evidence links, calls GO/NO-GO.
- **Engineering lead:** runs API reliability/latency/auth checks and confirms rollback readiness.
- **On-call owner:** verifies monitoring + alert path.
- **Growth/CMO owner:** verifies funnel events and launch-copy surfaces.

---

## 0) Environment prep (required)

Run from repo root unless noted.

```bash
export BASE_URL="https://doubow-production.up.railway.app"
export WEB_URL="https://doubow.vercel.app"
export DOUBOW_LAUNCH_PROBE_TOKEN="<fresh_clerk_jwt_without_Bearer>"
```

Expected:
- All env vars set.
- Token has enough validity window for probe runs.

Owner: Engineering lead

---

## 1) API liveness/readiness

```bash
curl -sS "$BASE_URL/healthz"
curl -sS "$BASE_URL/ready" | python3 -m json.tool
```

Expected:
- `/healthz` returns `{"status":"ok"}` (or equivalent 200 liveness payload).
- `/ready` shows:
  - `"status": "ready"`
  - `"postgres": "ok"`
  - `"redis": "ok"`
  - `background_durability.send_mode = "celery"`
  - `background_durability.autopilot_mode = "celery"`
  - `background_durability.enqueue = "ok"`

Owner: Engineering lead

---

## 2) Auth-path health (P0-2)

```bash
AUTH_PROBE_ITERATIONS=1 AUTH_PROBE_SLEEP_SECONDS=0 make -C backend auth-probe
```

Expected:
- Auth probe endpoints are `200` for:
  - `/v1/me/debug`
  - `/v1/me/applications`
  - `/v1/me/approvals`
  - `/v1/agents/chat`
- No auth-path 5xx regressions in logs.

Owner: Engineering lead

---

## 3) Core reliability + latency (P0-1, P1-4)

```bash
LAUNCH_PROBE_ITERATIONS=20 LAUNCH_PROBE_SLEEP_SECONDS=2 make -C backend launch-probe
```

Expected:
- Combined 5xx and route-level 5xx pass launch checklist thresholds.
- Samples are authenticated 2xx (not dominated by 401 responses).
- Reported p95 values meet targets:
  - `/v1/jobs` <= 1500ms
  - `/v1/me/applications` <= 1000ms
  - `/v1/me/approvals` <= 1000ms
  - `/v1/agents/chat` first payload <= 3000ms; typical full <= 15000ms

Owner: Engineering lead

---

## 4) Monitoring + alert path (P1-6)

```bash
curl -sS "$BASE_URL/metrics" > /tmp/doubow-metrics.txt
make -C backend monitoring-drill-report
```

Expected:
- `/metrics` returns successfully.
- Monitoring drill report includes incident detection timestamps and alert-route evidence.
- On-call acknowledgement link is attached in tracker evidence.

Owner: On-call owner

---

## 5) OAuth reconnect spot check (Step 7)

API preflight:

```bash
curl -sS "$BASE_URL/v1/integrations/google/status" -H "Authorization: Bearer $DOUBOW_LAUNCH_PROBE_TOKEN"
curl -sS "$BASE_URL/v1/integrations/linkedin/status" -H "Authorization: Bearer $DOUBOW_LAUNCH_PROBE_TOKEN"
```

Expected:
- Endpoints respond without `server_misconfigured`/5xx errors.
- Reconnect flows are already verified in runbook evidence:
  - `docs/operations/oauth-hardening-reconnect-runbook.md`

Owner: Integrations owner

---

## 6) Funnel telemetry smoke (marketing/data)

Run a short manual path in web UI:
1) open pricing section
2) toggle monthly/yearly
3) click pricing CTA
4) open onboarding and click a step
5) click settings reconnect or support link

Then verify event ingestion health through backend logs/telemetry sink (PostHog or internal event store).

Expected:
- New launch events appear with properties from `docs/operations/funnel-event-map.md`:
  - `pricing_interval_toggled`
  - `pricing_cta_clicked`
  - `pricing_billing_link_clicked`
  - `onboarding_step_clicked`
  - `onboarding_skip_clicked`
  - `settings_reconnect_clicked`
  - `settings_contact_support_clicked`

Owner: Growth/CMO owner

---

## 7) Final GO/NO-GO checkpoint

Decision command ritual:

```bash
echo "P0-1: <green|red>"
echo "P0-2: <green|red>"
echo "P0-3: <green|red>"
echo "P1-4: <green|red>"
echo "P1-5: <green|red>"
echo "P1-6: <green|red>"
echo "Step7 OAuth: <green|red>"
```

Expected:
- **GO only when all gates are green**.
- If any P0/P1/Step7 gate is red -> **NO-GO** and document corrective actions + owner + ETA.

Owner: Release manager (with Eng/Product/CMO signoff)

---

## Evidence checklist (attach links in tracker)

- [ ] `/healthz`, `/ready`, `/metrics` outputs
- [ ] `auth-probe` output
- [ ] `launch-probe` output
- [ ] monitoring drill report + on-call ack
- [ ] OAuth reconnect verification evidence
- [ ] funnel telemetry smoke evidence
- [ ] signed GO/NO-GO decision memo

---

## Day-10 signoff table (fill live)

| Role | Name | Decision (GO / NO-GO) | Notes |
|---|---|---|---|
| Release manager | _(fill)_ | _(fill)_ | _(fill)_ |
| Engineering lead | _(fill)_ | _(fill)_ | _(fill)_ |
| On-call owner | _(fill)_ | _(fill)_ | _(fill)_ |
| Product owner | _(fill)_ | _(fill)_ | _(fill)_ |
| CMO/Growth owner | _(fill)_ | _(fill)_ | _(fill)_ |

