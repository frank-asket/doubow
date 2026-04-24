# SLOs, alerting, and incident response (Doubow API)

Operational baseline for **`backend/api_gateway`**. Tune targets per environment (staging vs production).

---

## Service level objectives (draft)

| Objective | Target | Measurement window | Notes |
|-----------|--------|----------------------|--------|
| API availability | 99.5% monthly | `GET /healthz` or synthetic probe | Exclude planned maintenance windows from numerator. |
| Authenticated API success rate | ≥ 99% of non-4xx responses are 2xx for sampled dashboard routes | 7-day rolling | Exclude `401/403` from “failure”; track `5xx` separately. |
| LLM dependency | OpenRouter call error rate &lt; 5% of attempts by `use_case` | 24h | From Prometheus `doubow_llm_calls_total` / `doubow_llm_call_duration_seconds` (`services/metrics.py`). |
| p95 API latency (representative GET) | &lt; 800 ms | 7-day | e.g. `GET /v1/me/dashboard` behind auth; tune for your hosting region. |

Document **promotion thresholds** when changing these numbers (who approves, link to changelog).

---

## Metrics and logs

| Source | Endpoint / path |
|--------|------------------|
| Prometheus scrape | `GET /metrics` on the API gateway process |
| Structured logs | Application logs (stdout in containers); correlate `request_id` / user id where present |
| Health | `GET /healthz` (liveness), `GET /ready` or readiness variant if configured (`test_health_readiness.py`) |

---

## Alert conditions (starting set)

Wire these in Prometheus + Alertmanager (or Datadog/New Relic equivalents). Example rule file: **`deploy/prometheus/doubow-api-alerts.example.yml`**.

| Alert | Condition (conceptual) | Severity |
|-------|-------------------------|----------|
| APIDown | `/healthz` fails N consecutive probes | critical |
| High5xxRate | ratio of 5xx &gt; 1% over 15m on ingress or app | critical |
| LLMFailureBurst | `llm_calls_total{status="error"}` rate spikes vs baseline | warning |
| DBConnectionExhaustion | readiness fails Postgres check | critical |
| PrepEvalRegression | nightly `semantic_precision_eval.py` job fails | warning (fix forward; optional PR gate with secrets) |

Page **only** critical alerts after hours; warnings go to Slack/email per team policy.

---

## Incident response (lightweight)

1. **Acknowledge** in the incident channel; assign **incident lead**.
2. **Stabilize**: scale/restart instances, toggle **feature flags** (semantic scoring, LangGraph autopilot) off if documented in deploy notes.
3. **Communicate**: internal status + external message if user-visible.
4. **Mitigate**: rollback to last known-good image **or** forward-fix with patch; follow **`docs/capstone-readiness.md` §2 Rollback**.
5. **Post-incident**: short retro (root cause, action items); update SLOs or alerts if noisy/missed.

---

## RLS and database role (production)

Application code scopes by `user_id` (see **`tests/test_user_data_isolation.py`**). For defense in depth:

- Run migrations and app traffic with a **non-superuser** Postgres role.
- Enable and verify **Row Level Security** policies if your deployment uses them; smoke-test “user A cannot read user B’s rows” with the **same** role the app uses.

---

## Related

- **`docs/capstone-readiness.md`** — deployment checklist, risk register.
- **`README.md`** / **`backend/README.md`** — env vars and migrations.
