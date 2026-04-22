# Repository Structure

Canonical top-level map of this repository.

## Root folders

- `backend/` — backend runtime and service code (API gateway, migrations, backend scripts, backend compose).
- `backend/infra/` — Docker and proxy configs specific to the backend (dev Postgres/Redis stack, optional images).
- `apps/web/` — Next.js application (routes, components, public assets, build config).
- `packages/` — shared workspace packages (types/utilities).
- `docs/` — non-runtime documentation (architecture, design references, archive, onboarding).
- `.github/` — CI workflows and GitHub automation.
- `.git/` — git metadata.
- `.cursor/` — local Cursor IDE/project metadata.
- `.venv/` — local Python virtual environment for backend tooling/tests.

## Root files

- `.env` — local development environment variables and secrets (never commit real secrets).
- `.env.example` — template of required environment variables.
- `.gitignore` — ignore rules for local/generated artifacts.
- `README.md` — project overview, setup, and common workflows.
- `package.json` — monorepo workspace manifest and top-level npm scripts.
- `package-lock.json` — deterministic npm dependency lockfile.
- `turbo.json` — Turborepo task pipeline configuration.
