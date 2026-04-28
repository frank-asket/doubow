# OAuth Hardening + Reconnect Verification Runbook

Scope: production OAuth for Gmail and LinkedIn in Doubow.

- Backend API base: `https://doubow-production.up.railway.app`
- Frontend base: `https://doubow.vercel.app`
- Google callback route: `/v1/integrations/google/callback`
- LinkedIn callback route: `/v1/integrations/linkedin/callback`

---

## 1) Hardening Checklist (must pass before reconnect QA)

### A. Secret hygiene and rotation

1. Rotate leaked/old OAuth client secrets in provider consoles:
   - Google OAuth client secret
   - LinkedIn OAuth client secret
2. Update production env vars in Railway (backend service), then redeploy:
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `GOOGLE_OAUTH_CLIENT_SECRET`
   - `LINKEDIN_OAUTH_CLIENT_ID`
   - `LINKEDIN_OAUTH_CLIENT_SECRET`
3. Ensure cryptographic secrets are set and high-entropy:
   - `GOOGLE_OAUTH_STATE_SECRET`
   - `LINKEDIN_OAUTH_STATE_SECRET`
   - `GOOGLE_OAUTH_TOKEN_FERNET_KEY`
4. Verify no plaintext secrets remain in:
   - chat snippets
   - docs
   - committed `.env` files

### B. Redirect URI exactness (no mismatch)

Google Cloud OAuth client must include:

- `https://doubow-production.up.railway.app/v1/integrations/google/callback`

LinkedIn app OAuth redirect URL must include:

- `https://doubow-production.up.railway.app/v1/integrations/linkedin/callback`

Backend env vars must match provider console values exactly:

- `GOOGLE_OAUTH_REDIRECT_URI=https://doubow-production.up.railway.app/v1/integrations/google/callback`
- `LINKEDIN_OAUTH_REDIRECT_URI=https://doubow-production.up.railway.app/v1/integrations/linkedin/callback`

Frontend redirect env vars should point to settings UI:

- `GOOGLE_OAUTH_FRONTEND_REDIRECT_URI=https://doubow.vercel.app/settings`
- `LINKEDIN_OAUTH_FRONTEND_REDIRECT_URI=https://doubow.vercel.app/settings`

### C. Google consent screen constraints

1. If app is in Testing mode, add operator account(s) as Test Users.
2. Keep requested scopes minimal (currently from `GMAIL_API_SCOPES`):
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.compose`
3. Confirm consent screen branding/support email/policy URLs are complete.

### D. Backend config readiness check

`google_oauth_is_configured()` requires:

- client id
- client secret
- redirect uri
- state secret
- token fernet key

`linkedin_oauth_is_configured()` requires:

- client id
- client secret
- redirect uri
- state secret
- token fernet key

If any are missing, `/authorize` returns `503`.

---

## 2) Concrete Reconnect Verification Flow (prod)

Use one real user account in a clean browser session.

### Phase 1: API preflight

1. Confirm backend health:
   - `GET https://doubow-production.up.railway.app/healthz` returns `200`
2. Confirm authenticated integration status endpoints respond:
   - `GET /v1/integrations/google/status`
   - `GET /v1/integrations/linkedin/status`
3. Confirm authorize endpoints return an `authorization_url`:
   - `GET /v1/integrations/google/authorize`
   - `GET /v1/integrations/linkedin/authorize`

Expected:

- no 5xx
- no `server_misconfigured`

### Phase 2: UI reconnect verification

1. Open `https://doubow.vercel.app/settings`.
2. Click Gmail `Reconnect`.
3. Complete provider consent.
4. Confirm browser returns to:
   - `https://doubow.vercel.app/settings?google_connected=1`
5. Refresh settings and verify Gmail card remains connected.
6. Click LinkedIn `Reconnect`.
7. Complete provider consent.
8. Confirm browser returns to:
   - `https://doubow.vercel.app/settings?linkedin_connected=1`
9. Refresh settings and verify LinkedIn warning clears.

Failure signatures:

- `google_error=redirect_uri_mismatch`
- `google_error=token_exchange_failed`
- `linkedin_error=token_exchange_failed`
- `503 Google OAuth is not configured on this server`
- `503 LinkedIn OAuth is not configured on this server`

### Phase 3: Functional verification (no re-auth loop)

Gmail:

1. Trigger one email-channel approval send from Approvals.
2. Confirm success toast and delivery status (`provider_confirmed`, `provider_accepted`, or `draft_created`).
3. Retry a second send action in the same session and confirm no OAuth re-prompt.

LinkedIn:

1. Trigger one LinkedIn-channel approval.
2. Confirm handoff path succeeds (`send_provider=linkedin_email_handoff`, not failed).
3. Confirm no reconnect prompt appears immediately afterward.

### Phase 4: Persistence verification

After reconnect success, verify backend status endpoints still show connected after:

- page refresh
- logout/login
- 10-15 minute wait

Expected:

- Google `connected: true`, `google_email` present
- LinkedIn `connected: true`, `expires_at` present

---

## 3) Rollback / Incident response

If reconnect breaks production:

1. Disable provider connect entrypoint in UI (feature flag or temporary guard text).
2. Keep existing credentials untouched (do not mass-delete rows).
3. Restore last known-good redirect URIs and client secrets.
4. Redeploy backend.
5. Re-run Phase 1 preflight and Phase 2 reconnect verification.

---

## 4) Signoff template

- Date:
- Operator:
- Gmail reconnect: PASS/FAIL
- LinkedIn reconnect: PASS/FAIL
- Gmail action without re-auth: PASS/FAIL
- LinkedIn action without re-auth: PASS/FAIL
- Notes / failing callback URL:

