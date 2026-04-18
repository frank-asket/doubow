# Doubow

Multi-agent job search platform scaffold aligned with the Doubow architecture document.

## Structure
- `frontend`: Next.js UI
- `baseline`: backend/services scaffold (`api_gateway`, `model_service`, `worker_service`)

## Getting started
1. Copy `.env.example` to `.env`
2. Start infra from `infra/docker-compose.yml`
3. Run UI workspace with Turborepo (`frontend`)

## Repo Layout
- `frontend`: Next.js UI app.
- `baseline`: backend/service scaffold (`api_gateway`, `model_service`, `worker_service`).

Run commands from repo root:
- Frontend dev: `npm run -w frontend dev`
- Frontend build: `npm run -w frontend build`
- Baseline stack: `docker compose -f baseline/docker-compose.yml --env-file baseline/.env up --build`
- Baseline stop: `docker compose -f baseline/docker-compose.yml --env-file baseline/.env down`

## Database workflow (Supabase)

Set your Supabase Postgres connection string:

```bash
export DATABASE_URL="postgresql://<user>:<pass>@<host>:6543/postgres?sslmode=require"
```

One-command sync (migrate + seed + verify):

```bash
make db-sync
```

Equivalent explicit flow:

```bash
make db-migrate
make db-seed
make db-verify
```

The SQL scripts are:
- `scripts/db_seed.sql`
- `scripts/db_verify.sql`

## Implementation roadmap (priority order)

1. **Unify migration flow into startup/dev docs** *(implemented)*
   - Documented Supabase flow in this README.
   - Added one-command wrapper: `make db-sync`.

2. **Finish backend production hardening**
   - Replace remaining mock/demo API responses with DB-backed service logic.
   - Add typed error envelopes and idempotency tests for mutating endpoints.

3. **Auth + RLS alignment with Supabase**
   - Map Clerk identity to `users` records deterministically.
   - Define/enforce RLS policies for user-scoped tables (`applications`, `approvals`, `prep_sessions`, etc.).

4. **Seed realism + fixtures**
   - Expand seed to multi-user/multi-job realistic datasets.
   - Add reset/clean scripts for deterministic local/staging runs.

5. **E2E smoke suite**
   - Add Playwright smoke tests for landing, login, and authenticated dashboard routes:
     `discover`, `pipeline`, `approvals`, `agents`, `prep`.
   - Include Supabase-backed assertions.

6. **CI pipeline completion** *(partially implemented)*
   - Added CI checks for frontend lint/type-check/build.
   - Added backend migration-chain check (`alembic upgrade head --sql`).
   - Next: add backend tests and Supabase integration smoke check.
