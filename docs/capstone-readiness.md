# Capstone readiness package

Operational companion to **`docs/capstone-scoring-sheet.md`**. Use it for reviewer walkthroughs, deployment prep, and residual-risk tracking until production hardening is complete.

---

## 1. Evaluation metrics (dashboard notes)

These are the **measurable signals** referenced in the rubric. Wire them into PostHog, spreadsheets, or a BI tool as appropriate.

### Activation and product KPIs

| Metric | Definition | Primary source |
|--------|------------|----------------|
| Activation speed | Time from `resume_upload_succeeded` to `first_matches_ready` | PostHog events / `/v1/me/telemetry/activation-kpi` |
| Match quality proxy | Share of scored jobs with fit ≥ threshold among visible scored jobs | Discover summaries / DB |
| Approval conversion | `approved_and_sent / pending_approvals_created` | Approvals service + telemetry |
| API reliability | Error rate on key dashboard and mutating routes | Logs + telemetry error envelopes |

Operational roll-up endpoint for demos/reviews:

- `GET /v1/me/telemetry/launch-scorecard` — combines activation KPI, outcome KPI, and stability indicators into a single `go` / `watch` / `no_go` signal with reasons.

See **`docs/stack-decisions.md`** for baseline KPI definitions.

### Retrieval / scoring experiments (offline)

| Artifact | Purpose | Command / location |
|----------|---------|---------------------|
| Semantic precision vs baseline | Phase 3 gate: semantic blend uplift and precision floors | `scripts/semantic_precision_eval.py` |
| CI quality gates | Non-zero exit when thresholds fail | `--min-delta-pp`, `--min-semantic-precision` (see script help) |
| Scheduled eval | Nightly workflow (requires GitHub secret) | `.github/workflows/ci.yml` → job `semantic-eval-nightly`; set **`SEMANTIC_EVAL_USER_ID`** |

Example local run:

```bash
./.venv-test/bin/python scripts/semantic_precision_eval.py \
  --user-id "<clerk_user_id>" \
  --label-mode auto \
  --min-delta-pp 1.5 \
  --min-semantic-precision 0.70
```

Week-1-style snapshot:

```bash
./.venv-test/bin/python scripts/baseline_report.py
```

### LLM observability (backend)

| Signal | Where |
|--------|--------|
| Prometheus scrape | `/metrics` on API gateway |
| LLM call latency / outcomes by use case | `backend/api_gateway/services/metrics.py` + OpenRouter instrumentation |

### Generative text rubric (baseline CI gate)

Deterministic checks on model output **without** calling live LLMs in CI:

| Artifact | Purpose |
|----------|---------|
| `backend/api_gateway/services/generative_quality_rubric.py` | `assess_generative_text(text, use_case=…)` — min/max length, empty output, runaway repetition. |
| `backend/api_gateway/tests/test_generative_output_rubric.py` | Golden pass/fail strings; runs in default **`pytest backend/api_gateway/tests`**. |

**Residual gap (R1):** This is **not** semantic quality or LLM-as-judge scoring. Add golden-file fixtures for real model outputs or a judge harness when you need full “draft reads well” assurance.

---

## 2. Deployment checklist

Use before demoing on a shared environment or promoting toward production.

### Prerequisites

- [ ] **Env files**: `.env` (repo root) and `backend/.env` from `.env.example` / `backend/.env.example`; no secrets committed.
- [ ] **Clerk**: Issuer + JWKS aligned with frontend; sign-in flows tested for the target deployment URL.
- [ ] **Database**: `DATABASE_URL` points at target Postgres; run migrations (`make -C backend db-migrate` or Alembic per **`README.md`**).
- [ ] **Optional Redis**: Matches architecture assumptions for caches/worker coordination if enabled in your deployment profile.
- [ ] **OpenRouter**: `OPENROUTER_API_KEY` where LLM paths are exercised.
- [ ] **PostHog / Sentry** (if used): Keys and hosts set for frontend and backend per **`README.md`**.

### Smoke validation

- [ ] Web: app loads (`npm run dev:web` locally or deployed URL).
- [ ] API: **`GET /healthz`** OK.
- [ ] Auth: Protected routes require login; API rejects unauthenticated calls as expected.

### Database and tenancy (must-fix for production)

- [ ] App connects with a role that **does not bypass Postgres RLS** (avoid superuser for application traffic).
- [ ] Smoke test: user A cannot read user B’s rows on representative endpoints (application-layer coverage: **`tests/test_user_data_isolation.py`**; still validate RLS under the real DB role).

### Autopilot / LangGraph (optional feature path)

If **`USE_LANGGRAPH_AUTOPILOT`** and checkpoint flags are enabled, confirm:

- [ ] Migration applied so **`graph_checkpoint`** column exists on autopilot runs.
- [ ] **`POST /v1/me/autopilot/runs/{run_id}/resume`** documented for operators if workers can restart mid-run.

Details: **`backend/README.md`** (Autopilot scopes / LangGraph flags).

### Rollback

- [ ] Previous container image / release artifact tagged and retrievable.
- [ ] Alembic **downgrade** path noted for the release (or restore-from-backup plan if downgrade is unsafe).
- [ ] Feature flags documented so high-risk paths (LangGraph autopilot, semantic scoring) can be toggled off without redeploying code when possible.

---

## 3. Demo script (~12–18 minutes)

Rehearse this path so reviewers see **scope**, **safety**, and **AI depth** without dead ends. Adjust URLs if ports differ.

| Step | Action | Talking point |
|------|--------|----------------|
| 1 | Open landing or dashboard; sign in with Clerk | Multi-tenant job search copilot; human-in-the-loop |
| 2 | **`/resume`** — upload or view parsed profile | Structured extraction; optional LangChain path when enabled |
| 3 | **`/discover`** — scored roles | Fit scoring; semantic blend when feature-flagged |
| 4 | **`/pipeline`** — applications | Pipeline stages derived from durable state |
| 5 | **`/approvals`** — pending draft | HITL gate before outbound actions |
| 6 | **`/prep`** — prep for a real application | Scoped prep assist vs demo sessions (if split in UI) |
| 7 | **`/messages`** (Assistant / orchestrator chat); **`/agents`** redirects here | Unified chat + threads; cite **`GET /v1/agents/status`** if showing background agents |
| 8 | (Optional) Show **`GET /metrics`** or Grafana if wired | Operational maturity story |

**Fallback if LLM or OAuth flaky:** stay on discover/pipeline/approvals narrative; cite offline **`semantic_precision_eval.py`** results from a recent run.

---

## 4. Risk register (final)

| ID | Risk | Severity | Mitigation / owner |
|----|------|----------|-------------------|
| R1 | **Generative semantic quality** still partly subjective beyond rubric + retrieval metrics | Medium | Baseline rubric + pytest in CI; optional LLM-as-judge / golden exports for drafts |
| R2 | **Operations depth**: distributed tracing depth | Medium | **Delivered:** draft SLOs + alert examples — **`docs/operations/slo-and-incidents.md`**, **`deploy/prometheus/doubow-api-alerts.example.yml`**; wire alerts in your stack |
| R3 | **Deployment playbooks** thin (rollback, flag matrix, on-call) | Medium | Use §2 rollback checklist; expand runbook per hosting target |
| R4 | **RLS / auth** under production DB role | Medium | **Partial:** `test_user_data_isolation.py` proves service-layer scoping; complete RLS smoke with non-superuser role in staging |
| R5 | **Playwright / visual tests** may be local-only if not in default CI | Low | Run `npm run test -w @doubow/web` before major demos; consider adding job to CI |
| R6 | **Nightly semantic eval** depends on **`SEMANTIC_EVAL_USER_ID`** secret | Low | Document secret for maintainers; treat failing nightly as signal, not PR blocker |

---

## Related docs

- **`docs/capstone-scoring-sheet.md`** — rubric, weights, evidence map
- **`docs/operations/slo-and-incidents.md`** — SLOs, alerts, incident basics
- **`README.md`** — architecture, quick start, telemetry env vars
- **`backend/README.md`** — autopilot LangGraph flags, OAuth notes
- **`docs/stack-decisions.md`** — promotion gates for new dependencies
