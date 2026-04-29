# 20-Min Checkout E2E Script (Success + Cancel)

Purpose: run a fast, repeatable production check for checkout return contract and telemetry.

Scope covered:
- pricing intent handoff (`/auth/sign-up?redirect_url=...`)
- billing intent parsing (`intent`, `interval`)
- return contract (`/billing?checkout=success|cancel`)
- telemetry event (`billing_checkout_returned`)

---

## Timebox and owners

- Target duration: **15-20 minutes**
- Operator: Growth/CMO owner (with Engineering observer)

---

## Preconditions (2 minutes)

1. Production web is reachable:
   - `https://doubow.vercel.app`
2. Billing env is configured in deployment:
   - `NEXT_PUBLIC_BILLING_CHECKOUT_URL`
3. Provider return URLs are configured:
   - success -> `https://doubow.vercel.app/billing?checkout=success`
   - cancel -> `https://doubow.vercel.app/billing?checkout=cancel`
4. Test account exists (or can be created quickly) with dashboard access.

---

## Step A — Success path (6-8 minutes)

1. Open landing pricing section.
2. Select interval (monthly or yearly).
3. Click **Create account to upgrade** on Pro (or Business).
4. Complete auth/sign-up if prompted.
5. Confirm you land on billing with plan intent in URL (example):
   - `/billing?intent=pro&interval=monthly&source=pricing_card`
6. Click checkout CTA on billing.
7. Complete a successful checkout in provider flow.
8. Confirm return URL is:
   - `/billing?checkout=success`

Expected output:
- Billing page shows success banner: checkout completed.
- No blocking errors in page UI.
- Browser network includes a telemetry POST to:
  - `/v1/me/telemetry/events`
  - with `event_name = "billing_checkout_returned"`
  - and `properties.status = "success"`.

Evidence to save:
- Screenshot of billing success banner + URL bar.
- Screenshot of network payload for `billing_checkout_returned` (`status=success`).

---

## Step B — Cancel path (4-5 minutes)

1. Start checkout again from billing page.
2. Cancel/close in provider flow.
3. Confirm return URL is:
   - `/billing?checkout=cancel`

Expected output:
- Billing page shows cancel banner.
- Telemetry POST `/v1/me/telemetry/events` with:
  - `event_name = "billing_checkout_returned"`
  - `properties.status = "cancel"`.

Evidence to save:
- Screenshot of billing cancel banner + URL bar.
- Screenshot of network payload for `billing_checkout_returned` (`status=cancel`).

---

## Step C — Intent propagation check (2-3 minutes)

From pricing:
1. Trigger Pro yearly path.
2. Trigger Business monthly path.

Expected output:
- Billing URL carries matching intent:
  - `intent=pro|business`
  - `interval=yearly|monthly`
- Checkout URL opened from billing includes appended query params:
  - `plan`
  - `interval`
  - `source=billing_page`

Evidence to save:
- Two URL captures showing intent/interval correctness.

---

## Quick pass/fail rubric (1 minute)

- **PASS** if all are true:
  - success return contract works
  - cancel return contract works
  - telemetry event captured for both statuses
  - intent/interval propagation is correct
- **FAIL** if any item is missing or mismatched.

---

## Failure triage guide

- Missing return banner:
  - Verify return URL includes `checkout` query param.
- Missing telemetry event:
  - Verify `billing_checkout_returned` exists in backend schema and frontend telemetry type list.
  - Check auth/session; telemetry endpoint requires authenticated user context.
- Wrong plan/interval:
  - Verify pricing link includes `redirect_url` with `intent` + `interval`.
  - Verify billing page appends `plan` + `interval` to checkout URL.

---

## Checkbox-only run (launch day)

Use `docs/operations/launch-day-execution-checklist.md` (no prose).

---

## Record in tracker

Attach outcomes under:
- `docs/operations/launch-execution-tracker.md`
- Day-10 evidence in `docs/operations/launch-day-command-runbook.md`

