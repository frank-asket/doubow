import type { Page } from '@playwright/test'

/** Satisfies `ApiConnectionHealth` pings when `NEXT_PUBLIC_API_URL` points at a host with no server. */
export async function mockApiReachability(page: Page) {
  await page.route(
    (url: URL) => url.pathname === '/healthz' || url.pathname === '/ready',
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      })
    },
  )
}

export const dashboardFixture = {
  high_fit_count: 2,
  pipeline_count: 5,
  pending_approvals: 1,
  evaluated_this_week: 24,
  avg_fit_score: 3.9,
  applied_awaiting_reply: 3,
  total_scored_jobs: 10,
  response_rate_pct: 68,
}

export async function mockDashboardApis(page: Page) {
  await page.route((url: URL) => url.pathname === '/v1/me/dashboard', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(dashboardFixture),
    })
  })

  await page.route((url: URL) => url.pathname.startsWith('/v1/me/applications'), async (route) => {
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

  await page.route((url: URL) => url.pathname === '/v1/me/approvals', async (route) => {
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

  await page.route((url: URL) => url.pathname === '/v1/agents/status', async (route) => {
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

  await page.route((url: URL) => url.pathname === '/v1/agents/status/stream', async (route) => {
    await route.abort('failed')
  })
}

/** Routes Discover needs so the Job catalog shell + stats render without a running API. */
export async function mockDiscoverCatalogSupport(page: Page) {
  const now = new Date().toISOString()

  await page.route((url: URL) => url.pathname === '/v1/me/onboarding/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        state: 'ready',
        current_step: 'first_jobs_ready',
        eta_seconds: null,
        has_resume: true,
        first_jobs_ready: true,
      }),
    })
  })

  await page.route((url: URL) => url.pathname.startsWith('/v1/jobs'), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'job_1',
            title: 'AI Engineer',
            company: 'Acme Labs',
            location: 'Remote',
            url: 'https://example.com/job-1',
            discovered_at: now,
            salary_range: '$140k-$170k',
            score: {
              fit_score: 4.2,
              fit_reasons: ['Strong Python background'],
              risk_flags: [],
              dimension_scores: { tech: 4.5, culture: 3.8, seniority: 4.0, comp: 3.7, location: 4.2 },
              channel_recommendation: 'email',
            },
          },
          {
            id: 'job_2',
            title: 'ML Platform Engineer',
            company: 'Beta Systems',
            location: 'Paris',
            url: 'https://example.com/job-2',
            discovered_at: now,
            salary_range: '$120k-$150k',
            score: {
              fit_score: 3.4,
              fit_reasons: ['Platform overlap'],
              risk_flags: ['Onsite expectation'],
              dimension_scores: { tech: 3.6, culture: 3.1, seniority: 3.3, comp: 3.2, location: 3.8 },
              channel_recommendation: 'linkedin',
            },
          },
        ],
        total: 2,
        page: 1,
        per_page: 20,
      }),
    })
  })
}
