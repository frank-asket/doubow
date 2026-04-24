import { expect, test, type Page } from '@playwright/test'

const dashboardFixture = {
  high_fit_count: 2,
  pipeline_count: 5,
  pending_approvals: 1,
  evaluated_this_week: 24,
  avg_fit_score: 3.9,
  applied_awaiting_reply: 3,
  total_scored_jobs: 10,
  response_rate_pct: 68,
}

async function mockDashboardApis(page: Page) {
  await page.route('**/v1/me/dashboard', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(dashboardFixture),
    })
  })

  await page.route('**/v1/me/applications**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [],
        total: 0,
        page: 1,
        per_page: 20,
      }),
    })
  })

  await page.route('**/v1/me/approvals', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue()
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })

  await page.route('**/v1/agents/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          name: 'discovery',
          label: 'Discovery agent',
          description: 'Scans portals',
          status: 'active',
          message: 'Indexed',
          items_processed: 10,
        },
      ]),
    })
  })

  await page.route('**/v1/agents/status/stream', async (route) => {
    await route.abort('failed')
  })
}

test.describe('dashboard routes smoke', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('doubow.dashboard.onboarding.v2:anon', '1')
    })
    await mockDashboardApis(page)
  })

  test('pipeline page renders', async ({ page }) => {
    await page.goto('/pipeline')
    await expect(page.getByRole('heading', { name: 'Pipeline', exact: true })).toBeVisible()
  })

  test('approvals page renders', async ({ page }) => {
    await page.goto('/approvals')
    await expect(page.getByRole('heading', { name: 'Pending approvals', exact: true })).toBeVisible()
  })

  test('interview prep page renders', async ({ page }) => {
    await page.goto('/prep')
    await expect(page.getByRole('heading', { name: 'Interview prep', exact: true })).toBeVisible()
  })

  test('assistant page renders', async ({ page }) => {
    await page.goto('/messages')
    await expect(page.getByRole('heading', { name: 'Doubow Assistant', exact: true })).toBeVisible()
  })

  test('legacy /agents redirects to assistant', async ({ page }) => {
    await page.goto('/agents')
    await expect(page).toHaveURL(/\/messages/)
    await expect(page.getByRole('heading', { name: 'Doubow Assistant', exact: true })).toBeVisible()
  })
})
