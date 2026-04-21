# Stack Decisions: Now / Next / Later

This document defines the Week 1 baseline stabilization guardrails for `doubow`.
It is intentionally conservative: ship reliably with the current architecture first, then add libraries only when triggered by measurable bottlenecks.

## Objectives (Phase 1: Stabilize baseline)

- Freeze core architecture choices for the current milestone.
- Define baseline product and reliability KPIs.
- Set explicit promotion gates for introducing new stack components.
- Keep the delivery surface stable while iterating on quality.

## Decision Matrix

### Now (approved immediately)

- **API/App Core**
  - `FastAPI` + existing routers/services in `backend/api_gateway`
  - `SQLAlchemy` + `Alembic`
  - `Postgres` + existing tenancy/RLS posture
- **Agent Orchestration**
  - Existing custom agents (`discovery`, `scorer`, `tailor`, `writer`, `apply`, `prep_agent`, `monitor`, `orchestrator`)
- **Auth and User Scope**
  - Clerk identity + app-level user scoping
- **Telemetry**
  - Current PostHog + local telemetry event pipeline
  - Existing activation KPI endpoint
- **Quality Gates**
  - `next lint`, `tsc --noEmit`, `next build`
  - pytest suite
  - Playwright smoke/visual checks

**Rationale:** already integrated and green in current environment; lowest risk path to shipping.

### Next (add only with trigger)

- **Targeted structured LLM flow**
  - `langchain-core` in isolated boundaries where strict structured outputs are needed.
- **Semantic matching upgrades**
  - `sentence-transformers` for reranking/semantic similarity in fit scoring.
- **Worker reliability hardening**
  - stronger retry/backoff/timeouts and failure isolation.
- **Search upgrades in current DB**
  - improve Postgres search strategy before introducing external search infra.

**Trigger:** KPI regression or inability to meet targets with current stack.

### Later (defer by default)

- Multi-agent framework migration (`CrewAI`, `AutoGen`, `Haystack`) from custom orchestration.
- External search platform (`OpenSearch`/`Elasticsearch`).
- Dedicated model-serving infrastructure for self-hosted transformers.

**Trigger:** sustained scale/complexity limits that cannot be addressed incrementally.

## Baseline KPI Definitions (Week 1)

Track and report these as baseline metrics:

1. **Activation speed**
   - Definition: time from `resume_upload_succeeded` to `first_matches_ready`
   - Source: telemetry events / activation KPI endpoint
2. **Match quality proxy**
   - Definition: ratio of scored jobs with fit `>= 4.0` among visible scored jobs
   - Source: dashboard/discover summary data
3. **Approval conversion**
   - Definition: `approved_and_sent / pending_approvals_created`
   - Source: approvals/application services + telemetry
4. **Reliability**
   - Definition: API error rate for key dashboard routes and mutating endpoints
   - Source: API logs + telemetry error envelopes
5. **Build/Test health**
   - Definition: pass/fail for lint, type-check, build, pytest, Playwright smoke
   - Source: local/CI checks

## Baseline Targets (Phase 1)

- Lint/type/build: pass
- Backend tests: pass
- Playwright smoke: pass
- Activation KPI endpoint: returns valid `avg/latest/sample_size`
- No P0 regressions in `discover`, `pipeline`, `approvals`, `resume`, `agents`

## Promotion Gates For New Dependencies

A new library/framework can move from Next/Later to implementation only if all are true:

1. Problem statement is tied to a specific KPI miss.
2. A/B or before/after measurement plan exists.
3. Rollback path is documented.
4. Ownership is explicit (service/module + maintainer).
5. Test coverage is added for failure modes.

## Week 1 Execution Checklist

- [ ] Capture baseline values for all KPIs above.
- [ ] Store baseline snapshot in project notes/PR description.
- [ ] Keep stack frozen to "Now" list for this phase.
- [ ] Reject framework additions that do not pass promotion gates.
- [ ] Re-run full green checks at end of week and compare trend.

## Non-Goals (Week 1)

- Re-platforming agent orchestration to a new framework.
- Introducing external search infrastructure.
- Broad dependency expansion without measured need.
