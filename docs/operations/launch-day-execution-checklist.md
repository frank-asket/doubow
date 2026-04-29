# Launch day — execution checklist

- [ ] `BASE_URL` set (`https://doubow-production.up.railway.app`)
- [ ] `WEB_URL` set (`https://doubow.vercel.app`)
- [ ] `DOUBOW_LAUNCH_PROBE_TOKEN` set (valid JWT window)

- [ ] `curl "$BASE_URL/healthz"`
- [ ] `curl "$BASE_URL/ready"` (JSON ok)

- [ ] `AUTH_PROBE_ITERATIONS=1 AUTH_PROBE_SLEEP_SECONDS=0 make -C backend auth-probe`

- [ ] `LAUNCH_PROBE_ITERATIONS=20 LAUNCH_PROBE_SLEEP_SECONDS=2 make -C backend launch-probe`

- [ ] `curl "$BASE_URL/metrics"` → `/tmp/doubow-metrics.txt`
- [ ] `make -C backend monitoring-drill-report`

- [ ] `curl "$BASE_URL/v1/integrations/google/status" -H "Authorization: Bearer $DOUBOW_LAUNCH_PROBE_TOKEN"`
- [ ] `curl "$BASE_URL/v1/integrations/linkedin/status" -H "Authorization: Bearer $DOUBOW_LAUNCH_PROBE_TOKEN"`

- [ ] Pricing: toggle interval + CTA
- [ ] Onboarding: click a step
- [ ] Settings: reconnect or support link

- [ ] Prod web reachable (`WEB_URL`)
- [ ] `NEXT_PUBLIC_BILLING_CHECKOUT_URL` configured
- [ ] Success return URL → `/billing?checkout=success`
- [ ] Cancel return URL → `/billing?checkout=cancel`
- [ ] Test account ready

- [ ] Checkout success → `/billing?checkout=success` + success banner + `billing_checkout_returned` (`status=success`)
- [ ] Checkout cancel → `/billing?checkout=cancel` + cancel banner + `billing_checkout_returned` (`status=cancel`)
- [ ] Intent: Pro yearly URL params correct
- [ ] Intent: Business monthly URL params correct

- [ ] `echo` gate lines: P0-1, P0-2, P0-3, P1-4, P1-5, P1-6, Step7 OAuth → all green

- [ ] `/healthz`, `/ready`, `/metrics` artifacts
- [ ] `auth-probe` log
- [ ] `launch-probe` log
- [ ] Monitoring drill + on-call ack link
- [ ] OAuth / reconnect evidence link
- [ ] Funnel telemetry smoke evidence
- [ ] Checkout E2E screenshots / network captures
- [ ] Signed GO/NO-GO memo

| Role | Name | GO / NO-GO | Notes |
| --- | --- | --- | --- |
| Release manager | | | |
| Engineering lead | | | |
| On-call owner | | | |
| Product owner | | | |
| CMO/Growth owner | | | |
