# Backend

Backend services and data workflows for Doubow.

## Structure

- `api_gateway/` — FastAPI app, SQLAlchemy models, Alembic migrations, API tests.
- `model_service/` — model-facing service scaffold.
- `worker_service/` — async/background worker scaffold.
- `scripts/` — SQL scripts for seed/verify/reset/grants.
- `docker-compose.yml` — backend-local service orchestration.
- `infra/` — extra Docker assets: `docker-compose.yml` for a **standalone Postgres + Redis** stack (host Postgres on **5433**), plus optional `Dockerfile.api`, `Dockerfile.worker`, and `nginx.conf` samples.

## Run locally

### Database first

The API needs **PostgreSQL** at **`DATABASE_URL`** (defaults include `localhost:5433` in many `.env` examples). If uvicorn exits with **connection refused** on startup, start Postgres.

Paths are relative to your shell’s **current directory**:

- From the **repository root** (`doubow/`):

```bash
docker compose -f backend/infra/docker-compose.yml up -d
```

- From **`backend/`** (do **not** prefix `backend/` again):

```bash
docker compose -f infra/docker-compose.yml up -d
```

Then run migrations from repo root: `make -C backend db-migrate` (or `alembic upgrade head` from `backend/api_gateway` with `DATABASE_URL` set). **`DATABASE_URL` is normalized** for Alembic (psycopg2) and for `psql` seed/verify via `scripts/normalize_database_url.py`: asyncpg scheme + `?ssl=...` → libpq-friendly `sslmode=`. Supabase-style URLs work with the same **`db-migrate`** / **`db-sync`** as local Docker.

From repo root:

```bash
docker compose -f backend/docker-compose.yml --env-file backend/.env up --build
```

Stop:

```bash
docker compose -f backend/docker-compose.yml --env-file backend/.env down
```

From inside `backend/`:

```bash
docker compose --env-file .env up --build
docker compose --env-file .env down
```

### Postgres + Redis only (no app services)

Use this when you only need local databases (same port **5433** as documented in the repo-root `.env.example`).

From **repo root**:

```bash
docker compose -f backend/infra/docker-compose.yml up -d
docker compose -f backend/infra/docker-compose.yml down
```

From **`backend/`**:

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml down
```

## Database workflow

Set **`DATABASE_URL`** in `backend/.env` (or export it in your shell).

Migrate, seed, verify (local Docker **or** Supabase — URLs are normalized automatically):

```bash
make -C backend db-sync
```

Individual steps:

```bash
make -C backend db-migrate
make -C backend db-seed
make -C backend db-verify
```

**Aliases** (same recipes): `db-migrate-safe` → `db-migrate`, `db-sync-safe` → `db-sync`.

## API gateway tests

```bash
cd backend/api_gateway && PYTHONPATH=. python -m pytest tests/ -q
```

Focused autopilot parity check (legacy vs LangGraph item_results):

```bash
make -C backend api-test-autopilot-parity
```

Full autopilot suite (service, scopes, graph control-flow, execution/parity):

```bash
make -C backend api-test-autopilot
```

## OpenRouter model matrix

AI features are routed through OpenRouter with per-surface model settings. Configure in `backend/.env` (or repo-root `.env` when running uvicorn directly).

Core variables:

- `OPENROUTER_API_KEY` (required for AI features)
- `OPENROUTER_MODEL` (global fallback)
- `OPENROUTER_MODEL_CHAT`
- `OPENROUTER_MODEL_DRAFTS`
- `OPENROUTER_MODEL_PREP`
- `OPENROUTER_MODEL_RESUME`

Resolution order is:
1) surface-specific variable, 2) `OPENROUTER_MODEL`, 3) `ANTHROPIC_MODEL`.

**Default tiering in `config.py`** (no env overrides needed): dense **Qwen3** for global + cheap drafts, **DeepSeek R1 0528** for prep (reasoning-heavy), **Claude Sonnet 4.6** for streaming assistant chat, resume inherits the global model.

Explicit env copy-paste matching those defaults:

```env
OPENROUTER_MODEL=qwen/qwen3-32b
OPENROUTER_MODEL_CHAT=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_DRAFTS=qwen/qwen3-8b
OPENROUTER_MODEL_PREP=deepseek/deepseek-r1-0528
OPENROUTER_MODEL_RESUME=qwen/qwen3-32b
```

All-Claude profile (maximum consistency, higher cost):

```env
OPENROUTER_MODEL=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_CHAT=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_DRAFTS=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_PREP=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_RESUME=anthropic/claude-sonnet-4.6
```

Legacy cost-optimized profile (mini models for drafts + prep):

```env
OPENROUTER_MODEL=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_CHAT=anthropic/claude-sonnet-4.6
OPENROUTER_MODEL_DRAFTS=openai/gpt-4.1-mini
OPENROUTER_MODEL_PREP=openai/gpt-4.1-mini
OPENROUTER_MODEL_RESUME=anthropic/claude-sonnet-4.6
```

Runtime mapping:
- `chat` -> `/v1/agents/chat` orchestrator stream
- `drafts` -> approvals draft generation
- `prep` -> prep session + assist generation
- `resume` -> resume analysis (including LangChain path)

Safe diagnostics endpoint:
- `GET /v1/me/debug/ai-config` returns model resolution and OpenRouter config health (never returns API keys).

Prometheus (`GET /metrics`): assistant chat emits `doubow_assistant_tool_routing_total{phase=...}` (e.g. `keyword_match`, `llm_plan_hit`, `llm_plan_none`, `llm_skipped_no_key`) and `doubow_assistant_action_total{action=...,result=...}` (`success`, `policy_error`, `error`) for structured tool parity visibility.

## Provider ingestion (Adzuna + Greenhouse)

Protected endpoint:
- `POST /v1/jobs/providers/adzuna/ingest` (requires authenticated user)
- body:

```json
{
  "keywords": "software engineer",
  "location": "Berlin",
  "country": "de",
  "start_page": 1,
  "pages": 3,
  "per_page": 50
}
```

Protected Greenhouse endpoint:
- `POST /v1/jobs/providers/greenhouse/ingest` (requires authenticated user)
- body:

```json
{
  "board_tokens": ["notion", "openai"],
  "keywords": "backend engineer",
  "location": "Remote",
  "start_page": 1,
  "pages": 2,
  "per_page": 50
}
```

Cron-friendly preset endpoints (authenticated; catalog writes use `JOB_CATALOG_INGESTION_USER_ID`, not the caller):

- **Adzuna:** `POST /v1/jobs/providers/adzuna/ingest/preset?preset=hourly` or `preset=daily`
  - Optional query overrides: `keywords`, `location`, `country`, `start_page`
- **Greenhouse:** `POST /v1/jobs/providers/greenhouse/ingest/preset?preset=hourly` or `preset=daily`
  - Optional query overrides: `keywords`, `location`, `start_page`
  - Optional `boards=token1,token2` to override `GREENHOUSE_BOARD_TOKENS` for that run
- **Both providers in one call:** `POST /v1/jobs/providers/catalog/ingest/preset?preset=hourly|daily` (existing multi-source route)

Examples:

```bash
curl -sS -X POST "$API_URL/v1/jobs/providers/adzuna/ingest/preset?preset=hourly" \
  -H "Authorization: Bearer $CRON_JWT"

curl -sS -X POST "$API_URL/v1/jobs/providers/greenhouse/ingest/preset?preset=hourly" \
  -H "Authorization: Bearer $CRON_JWT"
```

Preset routes normalize provider results, snapshot raw source payloads, and upserts jobs into the shared catalog.
Each page fetch is recorded in `job_ingestion_runs` and raw provider rows in `job_source_records`.
Greenhouse uses the same storage path and cross-provider dedupe skeleton before upsert.

One-shot score refresh endpoint (after resume/profile updates):
- `POST /v1/jobs/recompute-scores` (authenticated user only)
- Rebuilds existing template-backed `job_scores` for the caller using current resume/profile signals.

Lightweight scheduler wrappers:
- Adzuna: `python backend/scripts/adzuna_ingestion_runner.py --mode once --pages 2`
- Adzuna: `python backend/scripts/adzuna_ingestion_runner.py --mode hourly --pages 3 --keywords "backend engineer"`
- Greenhouse: `python backend/scripts/greenhouse_ingestion_runner.py --mode once --pages 2`
- Greenhouse: `python backend/scripts/greenhouse_ingestion_runner.py --mode hourly --boards "notion,openai" --pages 2`
- Scores: `python backend/scripts/recompute_job_scores.py --user-id <USER_ID>`

Required env vars:
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`

Optional env vars:
- `ADZUNA_COUNTRY` (default `gb`)
- `ADZUNA_RESULTS_PER_PAGE` (default `50`)
- `ADZUNA_INGEST_HOURLY_PAGES` / `ADZUNA_INGEST_DAILY_PAGES` (preset endpoint page depth)
- `ADZUNA_INGEST_DEFAULT_KEYWORDS` / `ADZUNA_INGEST_DEFAULT_LOCATION` (defaults when preset query omits overrides)
- `GREENHOUSE_BOARD_TOKENS` (comma-separated board slugs, e.g. `notion,openai,figma`)
- `GREENHOUSE_INGEST_HOURLY_PAGES` / `GREENHOUSE_INGEST_DAILY_PAGES` (Greenhouse preset endpoint page depth)
- `GREENHOUSE_RESULTS_PER_PAGE` (default `50`, max `100`)
- `GREENHOUSE_INGEST_DEFAULT_KEYWORDS` / `GREENHOUSE_INGEST_DEFAULT_LOCATION` (defaults when Greenhouse preset query omits overrides)
- `JOB_CATALOG_INGESTION_USER_ID` (default `catalog_ingestion_system`, used by scheduler script and preset endpoint)

### Troubleshooting “404” on `/v1/agents/chat`

The gateway defines `POST /v1/agents/chat`. If the browser reports **404**:

1. Restart uvicorn from **`backend/api_gateway`** with `PYTHONPATH=.` so an old process isn’t running.
2. Open **`http://localhost:8000/docs`** (or your port) and confirm **POST `/v1/agents/chat`** exists.
3. If using Docker, rebuild/restart the API container so it picks up current code.
4. Ensure **`NEXT_PUBLIC_API_URL`** points at this gateway (not another service).

## Outbound email (SMTP)

After a user **approves** an **email-channel** draft, the API can send via SMTP (see `services/outbound_email.py`). Configure in **`backend/.env`** (used by `docker compose`) and/or the repo-root **`.env`** (loaded by `config.Settings` when running `uvicorn` locally).

| Variable | Purpose |
|----------|---------|
| `SMTP_ENABLED` | `true` to connect to SMTP; `false` = dry-run (log only, still completes workflow). |
| `OUTBOUND_FROM_EMAIL` | Required for real send (verified sender with your provider). |
| `SMTP_HOST` / `SMTP_PORT` | Provider SMTP endpoint (often 587 + TLS or 465 + SSL). |
| `SMTP_USE_TLS` / `SMTP_USE_SSL` | Match provider: 587 usually `TLS=true`; 465 usually `SSL=true`, `TLS=false`. |
| `SMTP_USER` / `SMTP_PASSWORD` | Provider credentials. |
| `OUTBOUND_SEND_RECIPIENT_OVERRIDE` | Optional; send all test mail to one inbox. |
| `USE_CELERY_FOR_SEND` | `true` only if a Celery worker consumes Redis. |

Copy commented defaults from **`backend/.env.example`** or **`.env.example`** at repo root. Restart the API after changes.

## Gmail OAuth (alternative to SMTP)

Users can link a Google account so **email-channel** approvals use the Gmail API (`services/gmail_send_service.py`): **`gmail.compose`** creates drafts in the user’s mailbox (default approval handoff), and **`gmail.send`** sends messages directly. SMTP remains the fallback.

1. In Google Cloud Console, create an OAuth **Web** client and add redirect URI **`GOOGLE_OAUTH_REDIRECT_URI`** (must match exactly, e.g. `http://localhost:8000/v1/integrations/google/callback`).
2. Enable the **Gmail API** for the project. Under **OAuth consent screen**, include the scopes your backend requests (`gmail.send` and `gmail.compose`). Sensitive/restricted scopes may require verification for production users; testing mode can use trusted test users without full verification.
3. Set `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`, `GOOGLE_OAUTH_STATE_SECRET`, and `GOOGLE_OAUTH_TOKEN_FERNET_KEY` (see **`backend/.env.example`**). Optional: `GOOGLE_OAUTH_FRONTEND_REDIRECT_URI` (default `http://localhost:3000/settings` after OAuth). Optional: **`GMAIL_APPROVAL_HANDOFF`**=`draft` (save draft first) or `send` (send immediately).
4. From the app **Settings** page, **Connect Gmail** calls `GET /v1/integrations/google/authorize` and opens Google’s URL. After changing scopes on the backend, users should **disconnect and reconnect** so Google issues a refresh token covering the new scopes.

## Autopilot scopes

Autopilot **`scope`** (`schemas/autopilot.py`) controls which applications get draft generation in a run:

- **`all`** — up to 100 applications for the user (optionally filtered by `application_ids`).
- **`failed_only`** — only applications that **failed** in the **latest completed** autopilot run that has `item_results` (retry failed draft generations).
- **`gmail_failed_only`** — subset of those failures whose error text looks Gmail/OAuth-related (heuristic for send/compose issues).

LangGraph flags for autopilot execution:
- `USE_LANGGRAPH_AUTOPILOT=true` routes background autopilot execution through explicit LangGraph nodes.
- `USE_LANGGRAPH_AUTOPILOT_TRACE=true` emits node lifecycle trace logs (`start`/`end`/`error`) for debugging.
- `USE_LANGGRAPH_AUTOPILOT_MAX_RETRIES=2` sets retry budget for retryable node failures before persisting run failure.
- `USE_LANGGRAPH_AUTOPILOT_CHECKPOINT=true` (default) writes `graph_checkpoint` JSON after each successful node so a subsequent worker invocation can resume via `resume_entry_node` routing.
- `ORCHESTRATOR_CHAT_TRANSCRIPT_MAX_MESSAGES` / `ORCHESTRATOR_CHAT_TRANSCRIPT_MAX_CHARS` bound the tail of thread history sent to the orchestrator LLM.
- **Agent-native assistant:** `GET /v1/agents/capabilities` lists structured actions the assistant can execute (parity with core UI flows). Keyword routing handles slash commands and common phrases; when that misses and `ORCHESTRATOR_LLM_TOOL_ROUTING=true` (default), a small OpenRouter call classifies the message into the same tool catalog before falling back to prose-only chat.

When a checkpointed LangGraph run is stuck in **`running`** after a worker crash, **`POST /v1/me/autopilot/runs/{run_id}/resume`** (authenticated) re-enqueues execution. Requires a stored checkpoint when LangGraph checkpointing is enabled.

## Activation KPI via PostHog

When PostHog environment variables are configured, activation telemetry is mirrored to PostHog and the
`/v1/me/telemetry/activation-kpi` endpoint reads KPI values from PostHog events.

Required env vars:
- `POSTHOG_HOST`
- `POSTHOG_PROJECT_ID`
- `POSTHOG_PERSONAL_API_KEY` (read/query API)
- `POSTHOG_PROJECT_API_KEY` (capture API)
