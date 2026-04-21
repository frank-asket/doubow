# Doubow

> Multi-agent job search platform where AI drafts and humans approve.

## ✨ Overview

Doubow combines a modern Next.js frontend with a FastAPI backend to help users discover roles, score fit, prepare applications, and safely approve outbound actions.

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
  FE[Frontend\nNext.js App Router]
  CL[Clerk Auth]
  API[API Gateway\nFastAPI]
  DB[(Supabase Postgres)]
  RD[(Redis)]
  PH[(PostHog)]
  AG[Agent Services\nDiscover • Scoring • Writing • Apply • Prep • Monitor]

  U --> FE
  FE -->|JWT / session| CL
  FE -->|Bearer Clerk JWT| API
  API -->|Validate claims + ensure user| CL
  API --> DB
  API --> RD
  API --> AG
  AG --> DB
  AG --> RD
  FE --> PH
  API --> PH
```

**Request path (typical):**
- User interacts with dashboard routes in `frontend/`.
- Frontend sends authenticated requests to `backend/api_gateway`.
- FastAPI validates Clerk identity, scopes every read/write to `user_id`, and orchestrates domain services.
- Services persist state in Postgres, use Redis for transient/queue-friendly workflows, and emit telemetry to PostHog.

### Deployment View (Local)

```mermaid
flowchart TB
  FE[Frontend Dev Server\nlocalhost:3000]
  API[api_gateway container\nlocalhost:8000 -> :8080]
  PG[(postgres container\n:5432)]
  R[(redis container\n:6379)]
  W[worker/model containers]

  FE --> API
  API --> PG
  API --> R
  W --> PG
  W --> R
```

## 🧱 Frontend + Backend Stack

### Frontend (`frontend/`)
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
- PostHog-backed activation KPI endpoint

## 🗺️ Repo Map

- `frontend/` — web application
- `backend/` — API, models, migrations, scripts, workers
- `docs/` — architecture, design system, onboarding, product maps
- `infra/` — infrastructure configs

Primary references:
- `docs/structure.md`
- `docs/product-panels.md`
- `docs/architecture/daubo-architecture-claude.md`
- `docs/architecture/daubo-design-system.md`

## 🎨 Design, Icons, Animation

- Icon language: `lucide-react` for consistent UI semantics.
- Product visual style is documented in `docs/design.md`.
- Activation and dashboard surfaces use subtle UI motion (loading/progress/fade transitions).

Visual references you can embed in GitHub markdown:
- `docs/design-screens/target-daubo.png`
- `docs/design-screens/landing-daubo-full-redesign.png`
- `docs/design-screens/local-daubo-after-pixel-pass.png`

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

### 3) Start frontend

```bash
npm --prefix frontend run dev
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
- API health: `http://localhost:8000/healthz`
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
- Backend mirrors activation events and serves `activation-kpi` (avg/latest/sample size).

## 🛣️ Product Surfaces

- `/discover` — scored job discovery + onboarding states
- `/pipeline` — application tracking + integrity checks
- `/approvals` — human approval gate for outbound actions
- `/prep` — role-specific interview preparation
- `/resume` — resume upload, parse, preferences
- `/agents` — multi-agent status + orchestration context

## 📚 Documentation

- Architecture: `docs/architecture/`
- Design system: `docs/architecture/daubo-design-system.md`
- Product panel behavior: `docs/product-panels.md`
- Onboarding notes: `docs/onboarding.md`
- Stack decision matrix and baseline gates: `docs/stack-decisions.md`
