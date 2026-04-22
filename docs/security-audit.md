# Security Audit Notes

## Scope

- OAuth token storage
- Portal scanner SSRF posture

## OAuth Token Storage

- Google refresh tokens are encrypted at rest with Fernet (`GOOGLE_OAUTH_TOKEN_FERNET_KEY`).
- LinkedIn access tokens follow the same encrypted-at-rest pattern.
- OAuth state is signed and expiry-bound via HMAC state token verification.
- Credential rows are scoped to `user_id` with RLS-aware request context.

## SSRF Prevention

- `portal_scanner` now enforces `http/https` schemes only.
- Hostname resolution is checked before requests.
- Loopback/private/link-local/multicast IP targets are blocked by default.
- Escape hatch exists only via `PORTAL_SCANNER_ALLOW_PRIVATE_IPS=true` for local debugging.

## Follow-up Hardening

- Add outbound domain allowlist for scanner connectors.
- Add request body size limits and stricter per-host timeouts.
- Add explicit audit logging for blocked scanner targets.
