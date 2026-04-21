# Doubow

Multi-agent job search platform scaffold aligned with the Doubow architecture document.

## Structure
- `frontend`: Next.js UI
- `backend`: backend/services scaffold (`api_gateway`, `model_service`, `worker_service`)

## Getting started
1. Copy `.env.example` to `.env` (canonical local `DATABASE_URL` for Docker Postgres is in that file).
2. Start infra from `infra/docker-compose.yml` — Postgres is exposed on **host port 5433** so it does not fight a native Postgres on 5432.
3. Run UI workspace with Turborepo (`frontend`)

## Repo Layout
- `frontend`: Next.js UI app.
- `backend`: backend/service scaffold (`api_gateway`, `model_service`, `worker_service`).
- `docs`: product docs and design assets.
  - `docs/architecture`: architecture notes and evolving technical decisions.
  - `docs/design-screens`: visual references and screenshot passes.
  - `docs/archive`: historical source artifacts.
- Canonical repository map: `docs/structure.md`.

Run commands from repo root:
- Frontend dev: `npm run -w frontend dev`
- Frontend build: `npm run -w frontend build`
- Backend stack: `docker compose -f backend/docker-compose.yml --env-file backend/.env up --build`
- Backend stop: `docker compose -f backend/docker-compose.yml --env-file backend/.env down`

## Database workflow (Supabase)

Set your Supabase Postgres connection string:

```bash
export DATABASE_URL="postgresql://<user>:<pass>@<host>:6543/postgres?sslmode=require"
```

One-command sync (migrate + seed + verify):

```bash
make -C backend db-sync
```

Equivalent explicit flow:

```bash
make -C backend db-migrate
make -C backend db-seed
make -C backend db-verify
```

`make -C backend db-seed`, `make -C backend db-verify`, and `make -C backend db-reset-demo` normalize `DATABASE_URL` for `psql`: if you use SQLAlchemy’s async form (`postgresql+asyncpg://...`), the driver prefix is rewritten to `postgresql://` before calling `psql`.

To wipe only demo rows (`u_demo_*` / `j_demo_*`) and re-seed:

```bash
make -C backend db-reset-demo
```

The SQL scripts are:
- `backend/scripts/db_seed.sql` — idempotent demo users, jobs, applications, approvals, prep sessions
- `backend/scripts/db_verify.sql` — sanity checks after seed
- `backend/scripts/db_reset_demo.sql` — deletes demo fixtures (keeps catalog migration rows such as `jb_cat_*`)
- `backend/scripts/db_grant_app_role.sql` — optional template for a least-privilege app role (`doubow_app`) with table grants for RLS-safe production use

## Implementation roadmap (priority order)

1. **Unify migration flow into startup/dev docs** *(implemented)*
   - Documented Supabase flow in this README.
   - Added one-command wrapper: `make -C backend db-sync`.

2. **Finish backend production hardening**
   - Replace remaining mock/demo API responses with DB-backed service logic.
   - Add typed error envelopes and idempotency tests for mutating endpoints.

3. **Auth + RLS alignment with Supabase** *(implemented — app layer + Postgres policies)*
   - Clerk `sub` is normalized and stored as `users.id`; each request binds `app.current_user_id` for RLS (see `db/session.py`, migration `20260422_00_row_level_security`).
   - Use a **non-superuser** DB role for the API in production so RLS is not bypassed.

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
