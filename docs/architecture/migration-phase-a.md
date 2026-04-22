# Phase A Migration Guide (Non-Breaking)

Phase A introduces target structure scaffolding without changing runtime behavior.

## Current Source Of Truth

- Frontend runtime/source stays in `frontend/`.
- Backend runtime/source stays in `backend/api_gateway/`.

## New Mirror Entrypoints

- `apps/web`: workspace wrapper for frontend scripts.
- `apps/api`: workspace wrapper for backend scripts/tests.
- `packages/shared`: shared barrel entrypoint for future shared contracts.

## Where To Put New Code During Transition

- New product features: keep placing code in `frontend/` and `backend/api_gateway/` until the matching Phase B slice starts.
- Shared TypeScript contracts intended for cross-app use: place in `packages/shared/types/` and re-export if needed.
- Avoid creating duplicate implementations across legacy and mirrored paths.

## Root Commands Added In Phase A

- `npm run dev:web`
- `npm run dev:api`
- `npm run build:web`
- `npm run build:api`
- `npm run lint:web`
- `npm run test:api`

These commands route to existing implementations so behavior remains stable.
