# Phase A Migration Guide (Historical)

This document records the initial migration setup before the runtime cutover to `apps/web`.

## Current Source Of Truth

- Web runtime/source stays in `apps/web/`.
- Backend runtime/source stays in `backend/api_gateway/`.

## New Mirror Entrypoints

- `apps/web`: canonical web workspace.
- `apps/api`: workspace wrapper for backend scripts/tests.
- `packages/shared`: shared barrel entrypoint for future shared contracts.

## Where To Put New Code During Transition

- New product features: place web code in `apps/web/` and backend code in `backend/api_gateway/`.
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
