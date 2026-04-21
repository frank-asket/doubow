# Backend

Backend services and data workflows for Doubow.

## Structure

- `api_gateway/` — FastAPI app, SQLAlchemy models, Alembic migrations, API tests.
- `model_service/` — model-facing service scaffold.
- `worker_service/` — async/background worker scaffold.
- `scripts/` — SQL scripts for seed/verify/reset/grants.
- `docker-compose.yml` — backend-local service orchestration.
- `Makefile` — DB migration/seed helpers.

## Run locally

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

## Database workflow

From repo root:

```bash
make -C backend db-migrate
make -C backend db-seed
make -C backend db-verify
```

One-command sync:

```bash
make -C backend db-sync
```

## API gateway tests

```bash
cd backend/api_gateway && PYTHONPATH=. python -m pytest tests/ -q
```

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

## Activation KPI via PostHog

When PostHog environment variables are configured, activation telemetry is mirrored to PostHog and the
`/v1/me/telemetry/activation-kpi` endpoint reads KPI values from PostHog events.

Required env vars:
- `POSTHOG_HOST`
- `POSTHOG_PROJECT_ID`
- `POSTHOG_PERSONAL_API_KEY` (read/query API)
- `POSTHOG_PROJECT_API_KEY` (capture API)
