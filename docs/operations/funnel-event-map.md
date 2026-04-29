# Funnel Event Map (Launch)

Purpose: quick reference for marketing, product, and data teams to analyze launch funnel health using Doubow telemetry events.

Event ingestion endpoint: `POST /v1/me/telemetry/events`  
Primary source code: `apps/web/lib/telemetry.ts`, `apps/web/lib/api.ts`, `backend/api_gateway/schemas/telemetry.py`

---

## How to use this map

- Use these events to build stage conversion views from **landing intent** -> **account creation intent** -> **onboarding actions** -> **integration intent** -> **activation**.
- Keep all event names and property keys exact to avoid schema mismatch.
- Treat this as the launch baseline. Add new events only with an explicit KPI reason.

---

## Event reference

| Event name | Trigger (where) | Properties | KPI usage |
|---|---|---|---|
| `pricing_interval_toggled` | Pricing interval switch clicked in `apps/web/components/landing/Pricing.tsx` | `interval` (`monthly` \| `yearly`) | Pricing preference split, annual plan intent signal |
| `pricing_billing_link_clicked` | “Doubow plans & billing” link clicked in pricing section | `source` (currently `pricing_section_text_link`) | Mid-funnel intent from landing pricing copy |
| `pricing_cta_clicked` | Any plan CTA clicked in pricing cards | `tier`, `billing_interval`, `cta_label` | Top-of-funnel to sign-up intent by tier and interval |
| `onboarding_step_clicked` | Step CTA clicked in onboarding page (`/onboarding`) | `step`, `title`, `destination` | Onboarding progression, step drop-off diagnostics |
| `onboarding_skip_clicked` | “Skip to dashboard” clicked in onboarding | `destination` | Skip rate and onboarding bypass impact |
| `settings_reconnect_clicked` | Gmail/LinkedIn reconnect button clicked in settings | `provider` (`google` \| `linkedin`) | Integration friction and reconnect demand |
| `settings_contact_support_clicked` | “Contact support” clicked in settings account actions | `source` (currently `settings_account_actions`) | Support-demand proxy for account/settings friction |
| `billing_checkout_returned` | Billing page loaded with `checkout=success` or `checkout=cancel` query param | `status` (`success` \| `cancel`), `intent`, `interval` | Checkout completion/cancel outcome for monetization funnel |
| `resume_upload_started` | Resume upload starts (`apps/web/hooks/useResumeUpload.ts`) | `file_name`, `file_size` | Activation funnel: upload attempt volume |
| `resume_upload_succeeded` | Resume upload succeeds (`apps/web/hooks/useResumeUpload.ts`) | `file_name`, `file_size`, `source` | Activation funnel: successful profile creation |
| `discover_empty_viewed` | Discover empty state viewed (`apps/web/src/discover/page.tsx`) | _none_ | Match supply/quality risk indicator |
| `match_scoring_started` | Discover scoring state appears | `step` | Time-to-value progress instrumentation |
| `match_scoring_eta_shown` | ETA displayed during scoring | `eta_seconds` | Scoring latency visibility and expectation mgmt |
| `first_matches_ready` | Discover ready state reached | `duration_seconds`, `started_at`, `ready_at` | Activation success milestone; feeds activation KPI |

---

## Recommended launch dashboards

1. **Pricing intent funnel**
   - `pricing_cta_clicked` -> sign-up started/completed (external auth or product analytics join) -> `resume_upload_succeeded`
   - Breakdown: `tier`, `billing_interval`

2. **Checkout outcome funnel**
   - pricing intent events -> billing page -> `billing_checkout_returned`
   - Track `success` vs `cancel` ratio by `intent` and `interval`

3. **Onboarding completion funnel**
   - `onboarding_step_clicked` by `step`
   - `onboarding_skip_clicked` rate
   - Correlate with subsequent `resume_upload_succeeded` and `first_matches_ready`

4. **Integration friction monitor**
   - `settings_reconnect_clicked` by `provider`
   - `settings_contact_support_clicked`
   - Pair with OAuth status/support ticket volume where available

5. **Activation latency panel**
   - `resume_upload_succeeded` -> `first_matches_ready`
   - Reconcile with `/v1/me/telemetry/activation-kpi`

---

## Naming and governance rules

- Keep event names stable once dashboards depend on them.
- Add properties only when they serve a concrete KPI question.
- Never include secrets, tokens, or PII in event properties.
- If an event contract changes, update this document in the same PR.

---

## Clerk checkout return URL helper (tiny snippet)

If you are using Clerk Billing (or a Clerk-hosted checkout flow), set your return URLs so billing outcomes come back to Doubow with the expected contract:

- Success URL: `https://doubow.vercel.app/billing?checkout=success`
- Cancel URL: `https://doubow.vercel.app/billing?checkout=cancel`

Where to paste in Clerk dashboard:

1. Open Clerk Dashboard -> Billing / Plans (or checkout configuration for your plan).
2. In the checkout session return/redirect settings, set:
   - `success_url` = `https://doubow.vercel.app/billing?checkout=success`
   - `cancel_url` = `https://doubow.vercel.app/billing?checkout=cancel`
3. Save and run one test checkout + one canceled checkout to verify `billing_checkout_returned` events appear.

