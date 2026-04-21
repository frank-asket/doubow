# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/dashboard_routes.spec.ts >> dashboard routes smoke >> pipeline page renders
- Location: frontend/tests/dashboard_routes.spec.ts:74:7

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/pipeline", waiting until "load"

```

# Test source

```ts
  1  | import { expect, test, type Page } from '@playwright/test'
  2  | 
  3  | const dashboardFixture = {
  4  |   high_fit_count: 2,
  5  |   pipeline_count: 5,
  6  |   pending_approvals: 1,
  7  |   evaluated_this_week: 24,
  8  |   avg_fit_score: 3.9,
  9  |   applied_awaiting_reply: 3,
  10 |   total_scored_jobs: 10,
  11 | }
  12 | 
  13 | async function mockDashboardApis(page: Page) {
  14 |   await page.route('**/v1/me/dashboard', async (route) => {
  15 |     await route.fulfill({
  16 |       status: 200,
  17 |       contentType: 'application/json',
  18 |       body: JSON.stringify(dashboardFixture),
  19 |     })
  20 |   })
  21 | 
  22 |   await page.route('**/v1/me/applications**', async (route) => {
  23 |     await route.fulfill({
  24 |       status: 200,
  25 |       contentType: 'application/json',
  26 |       body: JSON.stringify({
  27 |         items: [],
  28 |         total: 0,
  29 |         page: 1,
  30 |         per_page: 20,
  31 |       }),
  32 |     })
  33 |   })
  34 | 
  35 |   await page.route('**/v1/me/approvals', async (route) => {
  36 |     if (route.request().method() !== 'GET') {
  37 |       await route.continue()
  38 |       return
  39 |     }
  40 |     await route.fulfill({
  41 |       status: 200,
  42 |       contentType: 'application/json',
  43 |       body: JSON.stringify([]),
  44 |     })
  45 |   })
  46 | 
  47 |   await page.route('**/v1/agents/status', async (route) => {
  48 |     await route.fulfill({
  49 |       status: 200,
  50 |       contentType: 'application/json',
  51 |       body: JSON.stringify([
  52 |         {
  53 |           name: 'discovery',
  54 |           label: 'Discovery agent',
  55 |           description: 'Scans portals',
  56 |           status: 'active',
  57 |           message: 'Indexed',
  58 |           items_processed: 10,
  59 |         },
  60 |       ]),
  61 |     })
  62 |   })
  63 | 
  64 |   await page.route('**/v1/agents/status/stream', async (route) => {
  65 |     await route.abort('failed')
  66 |   })
  67 | }
  68 | 
  69 | test.describe('dashboard routes smoke', () => {
  70 |   test.beforeEach(async ({ page }) => {
  71 |     await mockDashboardApis(page)
  72 |   })
  73 | 
  74 |   test('pipeline page renders', async ({ page }) => {
> 75 |     await page.goto('/pipeline')
     |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  76 |     await expect(page.getByRole('heading', { name: 'Pipeline', exact: true })).toBeVisible()
  77 |   })
  78 | 
  79 |   test('approvals page renders', async ({ page }) => {
  80 |     await page.goto('/approvals')
  81 |     await expect(page.getByRole('heading', { name: 'Pending approvals', exact: true })).toBeVisible()
  82 |   })
  83 | 
  84 |   test('interview prep page renders', async ({ page }) => {
  85 |     await page.goto('/prep')
  86 |     await expect(page.getByRole('heading', { name: 'Interview prep', exact: true })).toBeVisible()
  87 |   })
  88 | 
  89 |   test('agents page renders', async ({ page }) => {
  90 |     await page.goto('/agents')
  91 |     await expect(page.getByRole('heading', { name: 'Agent status', exact: true })).toBeVisible()
  92 |   })
  93 | })
  94 | 
```