# Career Ops -> Doubow Integration Spec

Date: 2026-05-06  
Owner: Product + API + Growth Engineering  
Status: Draft (implementation-ready)

## Goal

Integrate the strongest Career Ops patterns (scan -> score gate -> tailored draft flow) into Doubow without replacing existing architecture. Keep Doubow's human-approval safety model and existing dashboard surfaces.

---

## 1) Exact architecture touchpoints in current repo

### Backend touchpoints (existing)

- `backend/api_gateway/routers/jobs.py`
  - Existing discovery and provider ingest endpoints already support catalog refresh and scoring (`/v1/jobs/discover`, `/v1/jobs/providers/*`, `/v1/jobs/providers/catalog/ingest/preset`).
  - Integration anchor for user-triggered scan jobs.

- `backend/api_gateway/services/job_search_pipeline.py`
  - Existing multi-stage loop (`data_collection`, `resume_profile`, `job_matching`, `outbound_application`, `feedback`) is the right orchestration layer for Career Ops-like "run full loop now".
  - Integration anchor for "scan + score + queue candidates" composite action.

- `backend/api_gateway/routers/agents.py`
  - Existing `POST /v1/agents/job-search-pipeline/run` already executes coordinated pipeline.
  - Integration anchor for assistant-triggered slash commands.

- `backend/api_gateway/services/agent_tools_catalog.py`
- `backend/api_gateway/services/agent_action_executor.py`
- `backend/api_gateway/services/agent_tool_router.py`
  - Existing tool catalog and keyword/LLM routing support command-style actions.
  - Integration anchor for new commands like `/career-ops scan` and `/career-ops auto-pipeline`.

- `backend/api_gateway/services/portal_scanner.py`
- `backend/api_gateway/tasks/discovery_task.py`
  - `portal_scanner` currently validates URL reachability but returns an empty list.
  - Integration anchor for multi-source scan normalization and safe crawling controls.

- `backend/api_gateway/schemas/jobs.py`
- `backend/api_gateway/models/job.py`
  - Existing job + score schema already handles fit scores and source metadata.
  - Integration anchor for additional scan metadata and gating fields.

- `backend/api_gateway/routers/telemetry.py`
- `backend/api_gateway/models/telemetry_event.py`
- `backend/api_gateway/schemas/telemetry.py`
  - Existing event ingestion and analytics model already in place.
  - Integration anchor for scan/funnel instrumentation.

### Frontend touchpoints (existing)

- `apps/web/src/discover/page.tsx`
- `apps/web/src/discover/useJobs.ts`
  - Existing Discover list/filter/sort + refresh pattern.
  - Integration anchor for scan controls, fit-threshold preset, and "queue top N" UX.

- `apps/web/components/dashboard/MatchPipelineUpdateCard.tsx`
  - Existing "refresh everything" action already maps to pipeline run API.
  - Integration anchor for new "scan + auto-pipeline" options.

- `apps/web/src/agents/page.tsx`
  - Existing assistant/chat surface is the best place for command-style Career Ops interactions.
  - Integration anchor for slash command suggestions and tool activity feedback.

- `apps/web/lib/api.ts`
  - Existing typed client API map.
  - Integration anchor for new endpoints and typed request/response contracts.

- `apps/web/lib/telemetry.ts`
  - Existing event dispatch now mirrored to backend + PostHog.
  - Integration anchor for new scan/pipeline conversion events.

---

## 2) API and schema additions

## 2.1 New API endpoints

### A) Run scan on demand (user-facing)

- **Method/Path**: `POST /v1/jobs/scan/run`
- **Purpose**: trigger a bounded multi-source scan aligned to user profile/preferences.
- **Request**:
  - `query?: string`
  - `location?: string`
  - `sources?: string[]` (default configured set)
  - `max_results?: number` (default 100, cap 500)
  - `min_fit_threshold?: number` (default 0, range 0-5)
  - `queue_top_n?: number` (default 0)
  - `channel?: "email" | "linkedin" | "company_site"` (used when queueing)
- **Response**:
  - `scan_run_id`
  - `fetched`
  - `inserted`
  - `updated`
  - `deduped`
  - `scored`
  - `kept_after_threshold`
  - `queued_to_pipeline`
  - `top_job_ids: string[]`
  - `duration_ms`

Implementation files:
- add route in `backend/api_gateway/routers/jobs.py`
- add service orchestrator in `backend/api_gateway/services/job_discovery_service.py` (or new `career_ops_service.py`)

### B) Scan run status/history

- **Method/Path**: `GET /v1/jobs/scan/runs?limit=20`
- **Purpose**: show latest scan runs and outcomes in UI.
- **Response**: list of runs with status, counts, duration, threshold, source mix.

Implementation files:
- add route in `backend/api_gateway/routers/jobs.py`
- persistence model + queries in new files under `backend/api_gateway/models/` + service.

### C) Assistant command endpoint (optional if routed via existing tools)

No new endpoint required if implemented through existing `agents` action flow.  
Preferred: add new agent tool actions:
- `run_career_ops_scan`
- `run_career_ops_auto_pipeline`

Implementation files:
- `backend/api_gateway/services/agent_tools_catalog.py`
- `backend/api_gateway/services/agent_action_executor.py`
- `backend/api_gateway/services/agent_tool_router.py`

## 2.2 Schema additions (Pydantic)

Add to `backend/api_gateway/schemas/jobs.py`:
- `CareerOpsScanRunRequest`
- `CareerOpsScanRunResponse`
- `CareerOpsScanHistoryItem`
- `CareerOpsScanHistoryResponse`

Add to `apps/web/lib/api.ts`:
- matching TS types + client calls:
  - `jobsApi.runScan(...)`
  - `jobsApi.scanRuns(...)`

## 2.3 Data model additions (DB)

New table: `career_ops_scan_runs`
- `id` (uuid)
- `user_id` (fk users.id, indexed)
- `status` (`queued|running|done|failed`)
- `query`, `location`
- `sources_json`
- `max_results`, `min_fit_threshold`, `queue_top_n`
- `fetched`, `inserted`, `updated`, `deduped`, `scored`, `kept_after_threshold`, `queued_to_pipeline`
- `error_code`, `error_detail`
- `started_at`, `completed_at`, `created_at`

Optional table: `career_ops_scan_run_jobs`
- `run_id` (fk)
- `job_id` (fk)
- `fit_score_at_run`
- `kept_after_threshold` (bool)
- `queued` (bool)

Migration location:
- new Alembic revision in `backend/api_gateway/db/migrations/versions/`

## 2.4 Telemetry contract additions

Add event names in:
- `backend/api_gateway/schemas/telemetry.py`
- `apps/web/lib/api.ts` (TelemetryEventName)
- `apps/web/lib/telemetry.ts`

New events:
- `career_ops_scan_started`
- `career_ops_scan_completed`
- `career_ops_scan_failed`
- `career_ops_threshold_applied`
- `career_ops_queue_top_n_clicked`
- `career_ops_auto_pipeline_completed`

Required properties:
- `scan_run_id`
- `source_count`
- `fetched`, `scored`, `kept_after_threshold`, `queued_to_pipeline`
- `min_fit_threshold`
- `duration_ms`
- `status` (for completed/failed)

---

## 3) UI changes

## 3.1 Discover page (`apps/web/src/discover/page.tsx`)

Add "Career Ops mode" block above filters:
- CTA: `Scan now`
- Inputs:
  - query (optional)
  - location
  - sources multiselect (minimal v1: toggles)
  - `Min fit threshold` slider (0-5, default 4.0 preset available)
  - `Queue top N` numeric input (0-10)
- Output:
  - latest scan run summary card
  - top kept jobs count
  - queued count
  - link to pipeline

Behavior:
- call `jobsApi.runScan(...)`
- refresh discover list via existing `useJobs().refresh()`
- emit telemetry events for start/completion/failure

## 3.2 Match pipeline card (`apps/web/components/dashboard/MatchPipelineUpdateCard.tsx`)

Add optional toggle under current options:
- `Run scan before refreshing matches`

When enabled:
- execute `jobsApi.runScan(...)` first, then existing `jobSearchPipelineApi.run(...)`.
- show combined result summary in existing banner area.

## 3.3 Assistant page (`apps/web/src/agents/page.tsx`)

Add suggested prompts:
- `/career-ops scan`
- `/career-ops auto-pipeline --threshold 4.0 --queue-top 5`

No major layout change required; reuse existing tool call/result stream rendering.

## 3.4 Funnel/event map docs

Update:
- `docs/operations/funnel-event-map.md`

Add rows for all new `career_ops_*` events with KPI usage:
- scan throughput
- threshold yield ratio (`kept_after_threshold / scored`)
- queue conversion (`queued_to_pipeline / kept_after_threshold`)

---

## 4) Delivery shape (minimal, safe)

### PR 1 (backend contracts + telemetry)
- new scan run API and schemas
- DB migration + persistence
- agent tool additions
- telemetry event contract additions

### PR 2 (web UX)
- Discover "Career Ops mode" section
- Match Pipeline card toggle
- Assistant prompt additions
- docs update for event map

---

## 5) Acceptance criteria

- User can run a scan from Discover and receive deterministic run summary counts.
- Fit threshold can be applied server-side and reflected in counts.
- Optional queue-top-N creates pipeline entries safely using existing channel rules.
- Assistant supports command-like scan triggers through tool router.
- All new events appear in telemetry ingestion and PostHog mirror.
- Existing flows (Discover listing, Refresh Pipeline, Approvals) remain unchanged when new options are unused.

