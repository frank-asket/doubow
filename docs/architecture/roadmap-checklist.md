# Doubow Roadmap Execution Checklist

Status legend: `[x] implemented`, `[~] partial`, `[ ] missing`

## Phase 0 - Foundation

- [x] TASK-001 Init Turborepo monorepo
- [x] TASK-002 Next.js 14 + Tailwind + shadcn scaffold
- [x] TASK-003 FastAPI + pydantic-settings + async SQLAlchemy + Alembic scaffold
- [x] TASK-004 Docker compose with Postgres/Redis/API/worker
- [~] TASK-005 Supabase auth integration (current stack is primarily Clerk auth)
- [~] TASK-006 `POST /v1/me/resume` with Supabase Storage (upload exists; storage path is local FS)
- [x] TASK-007 Resume parser service (PDF + structured analysis pipeline present)
- [x] TASK-008 User preferences CRUD
- [x] TASK-009 Migrations for users/resumes/jobs/applications
- [x] TASK-010 Frontend onboarding flow (resume upload + preferences)

## Phase 1 - Discovery & Scoring

- [~] TASK-011 `DiscoveryAgent` scraper connectors (agent returns `connector_plan` + catalog hint; live scraper depth still incremental)
- [x] TASK-012 Job catalog + dedup on `(source, external_id)`
- [x] TASK-013 `ScorerAgent` scoring flow
- [x] TASK-014 `GET /v1/jobs` (`min_fit`, `location`, `page`)
- [x] TASK-015 Celery beat scheduled discovery (2x daily per user)
- [x] TASK-016 Discover panel UI
- [x] TASK-017 Zustand `jobStore` + SWR jobs hook
- [x] TASK-018 SSE score/agent streaming hooks
- [x] TASK-019 Redis score caching (TTL 6h)
- [x] TASK-020 Unit tests focused on scorer output schema guarantees (`job_score_mapping` clamps + `tests/test_job_score_schema.py`)

## Phase 2 - Pipeline & Integrity

- [x] TASK-021 Applications CRUD routes
- [~] TASK-022 `MonitorAgent` (summarizes stale + dedup rows when `applications` context is passed; deeper normalization TBD)
- [x] TASK-023 Integrity-check endpoint (dry-run + apply)
- [x] TASK-024 Pipeline panel UI
- [x] TASK-025 Integrity banner with richer row-jump UX (Jump to row → scroll + highlight `data-application-id`)
- [x] TASK-026 Supabase Realtime subscription for application status
- [x] TASK-027 Integration test for dry-run vs apply parity

## Phase 3 - Smart Prep & Idempotency

- [x] TASK-028 Redis-backed idempotency service
- [x] TASK-029 `autopilot_runs` table + migration
- [x] TASK-030 Autopilot idempotency contract (`202/200/409`)
- [x] TASK-031 Overlap prevention / distributed locking
- [x] TASK-032 `TailorAgent`
- [x] TASK-033 `WriterAgent`
- [x] TASK-034 Retry scopes (`failed_only`, `gmail_failed_only`)
- [x] TASK-035 Item-level diagnostics
- [x] TASK-036 Agents panel
- [x] TASK-037 Overlap + idempotency interaction tests

## Phase 4 - Approvals & Apply Handoff

- [x] TASK-038 `approvals` table + migration
- [x] TASK-039 `GET /v1/me/approvals`
- [x] TASK-040 `POST /v1/me/approvals/:id/approve`
- [x] TASK-041 `POST /v1/me/approvals/:id/reject`
- [x] TASK-042 Apply email handoff after approval (Gmail draft/send + SMTP fallback; Gmail draft marks applied; confirmations)
- [x] TASK-043 LinkedIn dispatch after approval (email handoff pack to candidate + `linkedin_email_handoff` provider metadata)
- [x] TASK-044 Gmail OAuth connect + refresh
- [x] TASK-045 LinkedIn OAuth connect flow
- [x] TASK-046 Gmail status/disconnect error UX hardening (Approvals banners, retry, Settings link; LinkedIn status hints)
- [x] TASK-047 Approvals panel with draft preview and channel badges
- [x] TASK-048 Channel-aware apply handoff UX completeness
- [x] TASK-049 Gmail status refresh control in handoff flow

## Phase 5 - Interview Prep

- [x] TASK-050 Prep question generation flow
- [x] TASK-051 STAR-R generation flow
- [~] TASK-052 Company brief depth (baseline implemented, enrichment still possible)
- [x] TASK-053 `prep_sessions` table + migration
- [x] TASK-054 Prep API read/generate routes
- [x] TASK-055 Prep panel UI

## Phase 6 - Orchestrator Chat & Observability

- [x] TASK-056 `POST /v1/agents/chat` SSE endpoint
- [x] TASK-057 Orchestrator prompt with user pipeline context
- [x] TASK-058 Run-history observability fields (`replayed_at`, `fresh_run`)
- [x] TASK-059 `GET /v1/agents/status` stream
- [x] TASK-060 Frontend orchestrator chat component
- [x] TASK-061 Run-history log UX in agents panel

## Phase 7 - Hardening & Production

- [x] TASK-062 Rate limiting per user
- [x] TASK-063 Supabase/Postgres RLS foundations
- [x] TASK-064 Structured logging + Sentry
- [x] TASK-065 Prometheus metrics + Grafana dashboard
- [~] TASK-066 Dev auth verification/unblock local QA
- [x] TASK-067 Python version pinning in `pyproject.toml`
- [~] TASK-068 End-to-end Playwright apply flow coverage (`pipeline_integrity.spec.ts` added; full resume→apply path still expandable)
- [x] TASK-069 OpenAPI/ReDoc docs
- [x] TASK-070 Security audit (OAuth storage + SSRF guardrails)
- [x] TASK-071 CI pipeline (lint/test/build/migrations)
- [x] TASK-072 Deployment config (Fly.io or Railway)

## Execution Order (Missing Tasks)

All previously missing tasks are now implemented.
