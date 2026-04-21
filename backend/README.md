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
