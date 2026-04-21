# Frontend

Next.js application for the Doubow product UI.

## Structure

- `app/` — App Router pages/layouts.
- `components/` — reusable UI components.
- `hooks/` — frontend hooks.
- `lib/` — API client and shared frontend utilities.
- `stores/` — client state stores.
- `public/` — static assets (`public/reference` for UI references).
- `tests/` — Playwright/browser tests.

## Run locally

From repo root:

```bash
npm run -w frontend dev
```

Build:

```bash
npm run -w frontend build
```

Lint and type-check:

```bash
npm run -w frontend lint
npm run -w frontend type-check
```

## Auth and API

- API base URL comes from `NEXT_PUBLIC_API_URL`.
- Authenticated calls use Clerk bearer tokens via `components/auth/ClerkApiAuthBridge.tsx` and `lib/api.ts`.
- Backend routes like `/v1/me/*` require a valid `Authorization: Bearer <Clerk JWT>`.
