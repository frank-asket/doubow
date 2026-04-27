# Doubow High-Level Flow

This diagram is the capstone-facing architecture view for the current implementation.
It reflects what is actually running in the repository today.

```mermaid
flowchart LR
  U[User Web App]
  FE[Frontend\nNext.js App Router]
  CL[Clerk\nAuth + Session]
  API[API Gateway\nFastAPI]
  AG[Domain/Agent Services\nDiscover • Scoring • Writing • Apply • Prep • Monitor]
  DB[(Supabase Postgres)]
  RD[(Redis)]
  LLM[LLM Provider\nOpenRouter/Anthropic]
  OAUTH[Channel Integrations\nGoogle OAuth • LinkedIn OAuth]
  AUTO[Autopilot Runs\nIdempotency • Run History • Resume API]
  LG[LangGraph Autopilot\nParity Graph (Optional)]
  PH[(PostHog)]
  SENTRY[(Sentry)]
  METRICS[/Metrics Endpoint/]

  U --> FE
  FE -->|Sign-in / session| CL
  FE -->|Bearer JWT| API
  API -->|JWT verify| CL
  API --> AG
  API --> OAUTH
  API --> AUTO
  API --> DB
  API --> RD
  API --> METRICS
  API --> SENTRY
  AG --> DB
  AG --> RD
  AG --> LLM
  AUTO --> LG
  AUTO --> DB
  AUTO --> RD
  LG --> DB
  FE --> PH
  API --> PH
```

## LangGraph Autopilot Status

LangGraph is now included as an optional **autopilot parity runtime** behind feature flags.

- Default execution remains service/router driven in FastAPI.
- When `USE_LANGGRAPH_AUTOPILOT` is enabled, autopilot runs through a LangGraph parity flow.
- When `USE_LANGGRAPH_AUTOPILOT_CHECKPOINT` is enabled, graph node progress/checkpoint state is persisted to Postgres for resumability.
- On LangGraph failure, execution can fall back to the legacy autopilot executor.

## Multi-step workflows without a graph runtime

The product flow **discover -> score -> draft -> approve -> send/prep** is represented as **explicit domain services plus durable state**, with optional LangGraph parity for autopilot execution:

- **Discover / score**: jobs and `job_scores` rows in Postgres; applications move to the **score** pipeline stage until a score exists for that user + job.
- **Draft / approve**: `approvals` rows hold draft text and human gate states (`pending` → `approved` / `edited`); branching (reject / discard) is normal application logic.
- **Send / prep**: approval timestamps and application status feed the **send_prep** stage; queues or workers can drive outbound actions without a separate workflow DB.
- **Autopilot parity path (optional)**: run lifecycle can be driven by LangGraph nodes with checkpoint/resume semantics while keeping Postgres as the durable source of truth.

Each `Application` returned by the API includes a derived **`pipeline_stage`** field (`score` | `draft` | `approve` | `send_prep`) computed from those tables—see `backend/api_gateway/workflow/pipeline.py`.

**Retries** for unstable outbound calls (e.g. OpenRouter HTTP) use bounded exponential backoff in `backend/api_gateway/workflow/retry.py`, wired through `services/openrouter.py`.

**Durable state** for runs and user-scoped entities remains **Postgres** (and **Redis** for caches/sessions/worker coordination where configured); no additional workflow database is required for the current scope.

## Local Deployment View

```mermaid
flowchart TB
  FE[Frontend Dev\nlocalhost:3000]
  API[api_gateway\nlocalhost:8000]
  PG[(Postgres)]
  R[(Redis)]
  W[Worker/Model Services]
  LG[LangGraph parity path\n(optional)]

  FE --> API
  API --> PG
  API --> R
  W --> PG
  W --> R
  API --> LG
  W --> LG
```
