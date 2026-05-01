import { expect, test } from '@playwright/test'

import { ONBOARDING_COMPLETED_INIT } from './e2e-onboarding'
import {
  mockApiReachability,
  mockDashboardApis,
  mockDiscoverCatalogSupport,
} from './mock-dashboard-api'

const mockResumeProfile = {
  parsed_profile: {
    summary: 'Summary from uploaded résumé (fixture).',
    skills: ['Python'],
    gaps: [],
  },
  preferences: {
    target_role: '',
    location: '',
    min_salary: undefined,
    seniority: 'Mid' as const,
    skills: [] as string[],
  },
  file_name: 'resume.pdf',
}

test.describe('smoke flows', () => {
  test('resume flow: upload + save preferences + analyze', async ({ page }) => {
    let resumeUploaded = false

    await mockApiReachability(page)
    await mockDashboardApis(page)

    const apiMatch =
      (path: string, exact?: boolean) => (url: URL) =>
        exact ? url.pathname === path : url.pathname.startsWith(path)

    await page.route(apiMatch('/v1/me/preferences', true), async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResumeProfile.preferences),
      })
    })

    await page.route(apiMatch('/v1/me/resume'), async (route) => {
      const url = new URL(route.request().url())
      if (url.pathname.includes('/analyze')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ analysis: 'Profile analysis generated for smoke test.' }),
        })
        return
      }

      const method = route.request().method()
      if (method === 'GET') {
        if (!resumeUploaded) {
          await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Resume not found' }),
          })
          return
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockResumeProfile),
        })
        return
      }

      if (method === 'POST') {
        resumeUploaded = true
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockResumeProfile),
        })
        return
      }

      await route.fallback()
    })

    await page.addInitScript(ONBOARDING_COMPLETED_INIT)

    await page.goto('/resume')
    await expect(page.getByRole('heading', { name: 'Resume Lab' })).toBeVisible()

    const saveButton = page.getByRole('button', { name: 'Save preferences' })
    await expect(saveButton).toBeDisabled()

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'resume.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 smoke'),
    })

    await expect(page.getByRole('heading', { name: 'resume.pdf' })).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Replace Resume' })).toBeVisible()
    await expect(saveButton).toBeEnabled()

    await saveButton.click()
    await expect(page.getByText('Preferences saved.')).toBeVisible()

    await page.getByRole('button', { name: 'Analyze Core' }).click()
    await expect(page.getByText('Profile analysis generated for smoke test.')).toBeVisible()
  })

  test('discover flow: stats render from live data shape', async ({ page }) => {
    const now = new Date().toISOString()

    await mockApiReachability(page)

    await page.route((url: URL) => url.pathname === '/v1/me/dashboard', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          high_fit_count: 1,
          pipeline_count: 1,
          pending_approvals: 0,
          evaluated_this_week: 148,
          avg_fit_score: 3.8,
          applied_awaiting_reply: 1,
          total_scored_jobs: 2,
          response_rate_pct: 50,
        }),
      })
    })

    await mockDiscoverCatalogSupport(page)

    await page.route('**/v1/me/applications**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'app_1',
              job_id: 'job_1',
              channel: 'email',
              status: 'pending',
              job_snapshot: { title: 'AI Engineer', company: 'Acme Labs' },
              created_at: now,
              updated_at: now,
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        }),
      })
    })

    await page.addInitScript(ONBOARDING_COMPLETED_INIT)

    await page.goto('/discover')
    await expect(page.getByRole('heading', { name: 'Job catalog' })).toBeVisible()

    await expect(page.locator('main p').filter({ hasText: /Top matches/ }).first()).toBeVisible()
    await expect(page.getByText('Acme Labs').first()).toBeVisible()
    await expect(page.getByText('AI Engineer').first()).toBeVisible()
  })
})
