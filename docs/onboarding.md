# Onboarding

Quick orientation for anyone working in this repository.

## Product surface

How the dashboard is meant to behave — panels, agents, and design intent — lives in **[`docs/product-panels.md`](docs/product-panels.md)**. Read that before changing Discover, Pipeline, Approvals, Prep, Resume, or Agents so UX and backend rules stay consistent.

## Monorepo layout

- **`frontend/`** — Next.js app (App Router), dashboard routes under `app/(dashboard)/`.
- **`backend/api_gateway/`** — FastAPI service, Postgres via SQLAlchemy/Alembic, migrations under `db/migrations/`.

## Database migrations

From the repository root (with your virtualenv activated):

```bash
python -m alembic upgrade head
```

Alembic reads merged `.env` files up the tree from `backend/api_gateway/db/migrations/`. For Supabase on IPv4-only networks, use a **Session pooler** URL on port **5432** in `ALEMBIC_DATABASE_URL` (see comments in `backend/api_gateway/db/migrations/env.py`).

## Common checks

```bash
npm run lint
npm run build
npm run test
```

Python tests for the API gateway:

```bash
cd backend/api_gateway && PYTHONPATH=. python -m pytest tests/ -q
```
