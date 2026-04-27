# Doubow

> Multi-agent job search platform where AI drafts and humans approve.

<p align="left">
  <img src="./apps/web/public/favicon.svg" alt="Doubow logo" width="36" height="36" />
</p>

## ✨ Overview

Doubow combines a modern Next.js web app with a FastAPI backend to help users discover roles, score fit, prepare applications, and safely approve outbound actions.

- 🧭 Discover scored jobs
- 🗂️ Track applications in pipeline
- ✅ Approve/reject drafts with HITL safety
- 🎯 Generate interview prep
- 📄 Parse resume into structured profile
- 🤖 Monitor all agent activity

## 🏗️ High-Level Architecture

```mermaid
flowchart LR
  U[User Browser]
  FE[Web App Next.js App Router]
  CL[Clerk Auth]
  API[API Gateway FastAPI CORS guard rate limit]
  LLM[OpenRouter LLM Models chat drafts prep resume]
  DB[(Supabase Postgres)]
  RD[(Redis)]
  PH[(PostHog)]
  SENTRY[(Sentry)]
  METRICS[Prometheus metrics endpoint]
  AG[Agent Services Discover Scoring Writing Apply Prep Monitor]
  OAUTH[Channel Integrations Google OAuth LinkedIn OAuth]
  SEM[Semantic Match Service feature flagged]
  EVAL[Offline Evaluator baseline versus semantic precision]
  LG[LangGraph autopilot parity graph optional]
  AUTO[Autopilot runs idempotency history resume API]

  U --> FE
  FE -->|JWT / session| CL
  FE -->|Bearer Clerk JWT| API
  API -->|Validate claims + ensure user| CL
  API --> DB
  API --> RD
  API --> AG
  API --> LLM
  API --> OAUTH
  API --> METRICS
  API --> SENTRY
  API --> AUTO
  AUTO --> LG
  AG --> DB
  AG --> RD
  AG --> LLM
  AG --> SEM
  AUTO --> DB
  AUTO --> RD
  LG --> DB
  EVAL --> DB
  EVAL --> SEM
  FE --> PH
  API --> PH
```

**Request path (typical):**
- User interacts with dashboard routes in `apps/web/`.
- Frontend sends authenticated requests to `backend/api_gateway`.
- FastAPI validates Clerk identity, applies localhost-safe CORS policy, scopes every read/write to `user_id`, and orchestrates domain services.
- OpenRouter LLM calls power orchestrator chat, draft generation, resume analysis, and interview-prep generation.
- Services persist state in Postgres, use Redis for transient/queue-friendly workflows, and emit telemetry to PostHog.
- Semantic matching is feature-flagged and blended into scoring when enabled; offline evaluator scripts compare baseline vs semantic precision.
- Approval handoff is channel-aware (email + LinkedIn) with explicit user approval before outbound actions.
- **Autopilot** runs as background work with idempotent keys and run history; when `USE_LANGGRAPH_AUTOPILOT` is enabled it executes through a **LangGraph** parity graph (`mark_running` → `resolve_targets` → `process_items` → `persist_*`) inside the API gateway/worker process. Optional **`USE_LANGGRAPH_AUTOPILOT_CHECKPOINT`** persists **`graph_checkpoint`** JSON in Postgres after each node so a replacement worker can resume; the UI/agents surface can call **`POST /v1/me/autopilot/runs/{run_id}/resume`** for stuck **`running`** runs when a checkpoint exists. On LangGraph failure the runner falls back to the legacy executor.
- Structured resume parsing can use optional **LangChain** boundaries when `USE_LANGCHAIN` is enabled (see `.env.example`).
- API exposes `/metrics` for Prometheus scraping and Sentry hooks for error observability.

### Deployment View (Local)

```mermaid
flowchart TB
  FE[Web App Dev Server localhost 3000]
  API[api gateway container localhost 8000 to 8080]
  LLM[OpenRouter HTTPS API]
  PG[(postgres container 5432)]
  R[(redis container 6379)]
  W[worker/model containers]

  FE --> API
  API --> PG
  API --> R
  API --> LLM
  W --> PG
  W --> R
```

Workers share Postgres, Redis, and LLM access with the gateway; **autopilot** (including optional **LangGraph** parity execution and checkpoint persistence) runs in these processes when enabled—see **`backend/README.md`** (Autopilot scopes / LangGraph flags).

## 🧱 Frontend + Backend Stack

### Web App (`apps/web/`)
- Next.js 14 App Router + TypeScript
- SWR data fetching + Zustand state
- Clerk auth UI integration
- PostHog client telemetry
- Icons via `lucide-react`
- Motion support via `framer-motion`

### Backend (`backend/`)
- FastAPI API gateway
- SQLAlchemy + Alembic migrations
- Postgres + Redis-friendly architecture
- Agent/service modules for discovery, scoring, writing, apply, prep, monitor
- Optional **LangGraph** autopilot runner (feature flags): parity graph nodes, **`graph_checkpoint`** on `autopilot_runs`, resume API for stuck runs
- Optional **LangChain** (`langchain-core`) for structured resume analysis when `USE_LANGCHAIN` is on
- PostHog-backed activation KPI endpoint

## 🗺️ Repo Map

- `apps/web/` — web application
- `backend/` — API, models, migrations, scripts, workers
- `docs/` — architecture, design system, onboarding, product maps
- `backend/infra/` — Docker snippets (Postgres/Redis dev stack, optional API/worker/nginx samples)

Primary references:
- `docs/structure.md`
- `docs/product-panels.md`
- `docs/architecture/doubow-high-level-flow.md`
- `docs/architecture/daubo-architecture-claude.md`
- `docs/architecture/daubo-design-system.md`

## 🎨 Design, Icons, Animation

- Main logo: Doubow mark (see `apps/web/public/favicon.svg` and `apps/web/components/Logo.tsx`).
- Icon language: `lucide-react` for consistent UI semantics across dashboard and landing.
- Product visual system is documented in `docs/design.md` and `docs/architecture/daubo-design-system.md`.
- Core motion primitives: fade/slide progress transitions, loading indicators, and low-amplitude hover elevation.
- Animation library: `framer-motion` (landing and interaction micro-motion).

Visual references you can embed in GitHub markdown:
- `docs/design-screens/target-daubo.png`
- `docs/design-screens/landing-daubo-full-redesign.png`
- `docs/design-screens/local-daubo-after-pixel-pass.png`
- `apps/web/public/reference/landing/hero-dashboard-real.png`

Animation guidance:
- Add short `.gif` demos in `docs/design-screens/` (Discover loading, Approvals flow, Dashboard interactions).
- Link them in this README under a “Demo” section when available.

## 🚀 Quick Start

### 1) Setup environment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

### 2) Install dependencies

```bash
npm install
```

### 3) Start web app

```bash
npm run dev:web
```

### 4) Start backend stack

```bash
docker compose -f backend/docker-compose.yml --env-file backend/.env up --build
```

Stop backend stack:

```bash
docker compose -f backend/docker-compose.yml --env-file backend/.env down
```

## 🧪 Local Validation

- Frontend: `http://localhost:3000`
- Auth route: `http://localhost:3000/auth/sign-up`
- API health: `http://localhost:8000/healthz` (liveness), `http://localhost:8000/ready` (readiness — Postgres + Redis status)
- Week 1 KPI snapshot: `./.venv-test/bin/python scripts/baseline_report.py`
- Phase 3 offline semantic precision eval:
  `./.venv-test/bin/python scripts/semantic_precision_eval.py --user-id <clerk_user_id>`
- Phase 3 with stronger outcome-proxy labels:
  `./.venv-test/bin/python scripts/semantic_precision_eval.py --user-id <clerk_user_id> --label-mode outcome`

## 🗄️ Database Workflow (Supabase/Postgres)

Set `DATABASE_URL`, then run:

```bash
make -C backend db-sync
```

Explicit steps:

```bash
make -C backend db-migrate
make -C backend db-seed
make -C backend db-verify
```

Reset demo fixtures only:

```bash
make -C backend db-reset-demo
```

## 📈 Telemetry And KPI (PostHog)

Frontend env:
- `NEXT_PUBLIC_POSTHOG_KEY`
- `NEXT_PUBLIC_POSTHOG_HOST`

Backend env:
- `POSTHOG_HOST`
- `POSTHOG_PROJECT_ID`
- `POSTHOG_PROJECT_API_KEY`
- `POSTHOG_PERSONAL_API_KEY`

Behavior:
- Frontend captures product events/pageviews.
- Backend mirrors product events and serves:
  - `GET /v1/me/telemetry/activation-kpi` (avg/latest/sample size for resume -> first matches),
  - `GET /v1/me/telemetry/outcome-kpi` (approval resolution/acceptance/send conversion rates),
  - `GET /v1/me/telemetry/launch-scorecard` (single GO/WATCH/NO_GO snapshot combining activation, outcomes, and stability signals).

## 🛣️ Product Surfaces

- `/discover` — scored job discovery + onboarding states
- `/pipeline` — application tracking + integrity checks
- `/approvals` — human approval gate for outbound actions
- `/prep` — role-specific interview preparation
- `/resume` — resume upload, parse, preferences
- `/agents` — Assistant (chat + background activity); primary nav uses jobs-first IA with this under **Assistant** in the sidebar
- `/billing` — subscription & billing (layout from `docs/mockup/subscription_billing`)

## 📚 Documentation

- Capstone rubric + readiness (eval notes, deployment checklist, demo script, risk register): `docs/capstone-scoring-sheet.md`, `docs/capstone-readiness.md`
- Architecture: `docs/architecture/` (including `docs/architecture/resilience.md` — health probes, rate limits, OpenRouter circuit behavior)
- Design system: `docs/architecture/daubo-design-system.md`
- Product panel behavior: `docs/product-panels.md`
- Onboarding notes: `docs/onboarding.md`
- Stack decision matrix and baseline gates: `docs/stack-decisions.md`
