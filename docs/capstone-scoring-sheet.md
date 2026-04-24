# Q1 Capstone Scoring Sheet

Use this sheet to evaluate capstone submissions consistently across reviewers.

## Scoring Scale (1-5)

- `1` = Not demonstrated / major gaps
- `2` = Emerging but incomplete
- `3` = Meets baseline expectations
- `4` = Strong and reliable
- `5` = Excellent, production-grade, clearly above baseline

## Weighted Criteria

Rate each criterion from 1-5, then multiply by its weight.

| Category | Weight | Criteria | Score (1-5) | Weighted Score |
|---|---:|---|---:|---:|
| Technical Depth | 20% | Problem selection and scope | 4.5 |  |
| Technical Depth | 20% | Architecture and design choices | 4.5 |  |
| Technical Depth | 20% | Prompt/model interaction quality | 3.5 |  |
| Technical Depth | 20% | Orchestration and control flow | 4.0 |  |
| Engineering Practices | 20% | Code quality | 4.0 |  |
| Engineering Practices | 20% | Logging and error handling | 4.0 |  |
| Engineering Practices | 20% | Unit/integration testing | 4.0 |  |
| Engineering Practices | 20% | Observability | 3.5 |  |
| Production Readiness | 15% | Solution feasibility | 4.0 |  |
| Production Readiness | 15% | Evaluation strategy | 3.0 |  |
| Production Readiness | 15% | Deployment readiness | 3.5 |  |
| Presentation | 15% | User interface quality | 4.5 |  |
| Presentation | 15% | Demo quality | 3.5 |  |
| Presentation | 15% | Communication clarity | 4.0 |  |

## Implementation Evidence Map (for raising scores to 5)

- **Technical Depth: Problem selection and scope**
  - `apps/web/src/prep/usePrepSessions.ts` + `apps/web/src/prep/page.tsx` — loads prep sessions per application via `prepApi`; STAR builder and readiness derive from the selected API-backed session, with UI fallbacks when none is loaded.
  - `backend/api_gateway/routers/prep.py` — `/capabilities`, scoped `/generate` and `/assist` routes tied to authenticated user + application IDs.
  - `apps/web/app/(dashboard)/messages/page.tsx` — unified **Doubow Assistant** chat (`streamOrchestratorChat`); single surface for mixed career intents aligned with product scope.
  - `backend/api_gateway/routers/agents.py` + `services/agent_chat_service.py` — orchestrator chat SSE, threaded transcript persistence, unified assistant system prompt.
- **Technical Depth: Prompt/model interaction quality**
  - `backend/api_gateway/services/openrouter.py` — `_USE_CASE_DEFAULTS` (`temperature`, `max_tokens`, `top_p`, optional `frequency_penalty` for drafts), debug logging with `use_case` + model, Prometheus hooks on success/failure paths.
  - `backend/api_gateway/services/llm_prompts.py` — centralized system prompts + **grounding rules** (anti-hallucination) per channel (draft email/LinkedIn, prep JSON/assist, resume analysis, orchestrator).
  - `backend/api_gateway/services/draft_service.py` / `prep_generation.py` / `resume_service.py` / `prep_assist_service.py` / `langchain_resume_analysis.py` — prompts imported from `llm_prompts`; LLM calls pass explicit `use_case` into OpenRouter helpers.
  - `backend/api_gateway/tests/test_openrouter_model_routing.py` — asserts `resolve_openrouter_model(use_case)`, payload merging, retries, and circuit-open behavior; see also `test_openrouter_slug.py` for model-id normalization.
- **Technical Depth: Orchestration and control flow**
  - `backend/api_gateway/services/openrouter.py` — `_USE_CASE_RUNTIME_POLICY` (timeouts), `async_retry` with backoff, `_circuit_state` / `_circuit_is_open` cooldown after consecutive failures.
  - `backend/api_gateway/tests/test_openrouter_model_routing.py` — circuit reset fixture; tests exercise failure paths and model selection (mocked HTTP, no live OpenRouter).
- **Production Readiness: Evaluation strategy**
  - `scripts/semantic_precision_eval.py` — CLI gates `--min-delta-pp`, `--min-semantic-precision`; non-zero exit on breach for CI.
  - `backend/api_gateway/services/generative_quality_rubric.py` + `tests/test_generative_output_rubric.py` — deterministic pass/fail on generated strings (length, emptiness, repetition) per `use_case`; semantic “reads well” quality remains optional/next step (`docs/capstone-readiness.md`).
- **Engineering Practices: Observability**
  - `backend/api_gateway/services/metrics.py` — Prometheus counters/histograms for LLM calls by `use_case`, `model`, `mode`, status.
  - `backend/api_gateway/services/openrouter.py` — records latency/outcomes on chat completion and streaming paths via `observe_llm_call`.
  - `docs/operations/slo-and-incidents.md` + `deploy/prometheus/doubow-api-alerts.example.yml` — draft SLOs, incident steps, example alert rules (`doubow_llm_calls_total`, etc.).
- **Production Readiness: Tenancy (application layer)**
  - `backend/api_gateway/tests/test_user_data_isolation.py` — list applications and prep detail scoped to owning user (complements Postgres RLS checks in staging).

## Category Scoring Formula

For each category:

`Category Score (0-100) = (Average criterion score / 5) * 100`

`Weighted Category Contribution = Category Score * Category Weight`

Overall score:

`Final Score (0-100) = Sum of all weighted category contributions`

## Quick Calculator Layout

Copy this into your notes/spreadsheet:

- Technical Depth avg: `____ / 5` -> contribution: `____ * 0.20`
- Engineering Practices avg: `____ / 5` -> contribution: `____ * 0.20`
- Production Readiness avg: `____ / 5` -> contribution: `____ * 0.15`
- Presentation avg: `____ / 5` -> contribution: `____ * 0.15`
- **Final Score**: `____ / 100`

Draft filled values:

- Technical Depth avg: `4.13 / 5` -> contribution: `82.5 * 0.20 = 16.5`
- Engineering Practices avg: `3.88 / 5` -> contribution: `77.5 * 0.20 = 15.5`
- Production Readiness avg: `3.50 / 5` -> contribution: `70.0 * 0.15 = 10.5`
- Presentation avg: `4.00 / 5` -> contribution: `80.0 * 0.15 = 12.0`
- **Weighted subtotal (per rubric weights listed): `54.5 / 70`**
- **Normalized final score: `77.9 / 100`**

## Rating Anchors by Category

### Technical Depth
- `1-2`: unclear scope, weak architecture rationale, brittle prompting
- `3`: clear scope, sensible architecture, acceptable prompt behavior
- `4-5`: strong decomposition, robust orchestration, thoughtful model controls

### Engineering Practices
- `1-2`: inconsistent code quality, minimal tests, weak failure handling
- `3`: readable code, baseline tests, reasonable logging and errors
- `4-5`: clean structure, meaningful test coverage, strong diagnostics and observability

### Production Readiness
- `1-2`: prototype only, little feasibility evidence, no deployment path
- `3`: realistic feasibility, basic evaluation, plausible deployment plan
- `4-5`: clear rollout strategy, rigorous evaluation, operational confidence

### Presentation
- `1-2`: unclear narrative, fragile demo, weak stakeholder communication
- `3`: understandable story and functional demo
- `4-5`: concise narrative, strong live demo, confident communication of trade-offs

## Reviewer Notes

- Key strengths:
  - Clear AI engineering scope with realistic product workflow (discover, scoring, approvals, prep).
  - Solid architecture decomposition (Next.js web app, FastAPI API gateway, Clerk auth, Postgres + Redis).
  - Strong safety posture improvements: user-scoped tenancy, typed error envelopes, idempotency checks, integration tests.
  - Dashboard UX quality significantly improved with cross-breakpoint visual regression coverage.
- Key risks:
  - Evaluation strategy for LLM quality is still light (limited quantitative quality benchmarks and acceptance gates).
  - Observability is good for events but not yet full production ops (alerts, SLOs, tracing depth).
  - Deployment hardening and rollback playbooks need tighter explicit documentation.
- Must-fix before production (status):
  - **Generative QA:** Baseline rubric + CI tests **delivered**; add LLM-as-judge / exported golden outputs when you need semantic scoring beyond length/repetition gates.
  - **SLOs / incidents / alerts:** Draft **delivered** in `docs/operations/slo-and-incidents.md` and example Prometheus rules; **wire** alerts and tune thresholds in your environment.
  - **Auth / RLS:** Service-layer isolation tests **delivered**; **still validate** Postgres RLS + app DB role in staging (non-superuser).
- Recommended next step:
  - Delivered: `docs/capstone-readiness.md` (eval metrics notes, deployment checklist, demo script, risk register).
