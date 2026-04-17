# Doubow

Multi-agent job search platform scaffold aligned with `Daubo Architecture - Claude.md`.

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
