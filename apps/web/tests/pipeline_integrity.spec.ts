import { expect, test } from '@playwright/test'

import { ONBOARDING_COMPLETED_INIT } from './e2e-onboarding'

test.describe('pipeline integrity', () => {
  test('integrity preview jump scrolls to application row', async ({ page }) => {
    const now = new Date().toISOString()
    const jobBase = {
      source: 'manual' as const,
      external_id: 'ext-1',
      title: 'Platform Engineer',
      company: 'Riverstone Labs',
      location: 'Remote',
      description: 'Build reliable systems.',
      url: 'https://example.com/job/1',
      discovered_at: now,
    }
    const score = (jobId: string) => ({
      job_id: jobId,
      fit_score: 4.0,
      fit_reasons: ['Strong fit'],
      risk_flags: [] as string[],
      dimension_scores: { tech: 4, culture: 4, seniority: 4, comp: 4, location: 4 },
      channel_recommendation: 'email' as const,
      scored_at: now,
    })

    await page.route('**/v1/me/applications**', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.fallback()
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'app-stale-1',
              user_id: 'user-e2e',
              job: { ...jobBase, id: 'job-1', external_id: 'ext-1' },
              score: score('job-1'),
              status: 'pending',
              channel: 'email',
              last_updated: now,
              is_stale: true,
              pipeline_stage: 'score',
            },
            {
              id: 'app-fresh-2',
              user_id: 'user-e2e',
              job: { ...jobBase, id: 'job-2', external_id: 'ext-2', title: 'Data Engineer' },
              score: score('job-2'),
              status: 'saved',
              channel: 'email',
              last_updated: now,
              is_stale: false,
              pipeline_stage: 'score',
            },
          ],
          total: 2,
          page: 1,
          page_size: 20,
        }),
      })
    })

    await page.route('**/v1/me/applications/integrity-check', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.fallback()
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          mode: 'dry_run',
          summary: { duplicates: 0, stale: 1, status_fixes: 0 },
          changes: [
            {
              type: 'mark_stale',
              application_ids: ['app-stale-1'],
              keep_id: 'app-stale-1',
              reason: 'Stale application row (e2e fixture)',
            },
          ],
        }),
      })
    })

    await page.addInitScript(ONBOARDING_COMPLETED_INIT)

    await page.goto('/pipeline')
    await expect(page.getByRole('heading', { name: 'My applications' })).toBeVisible()
    await expect(page.getByText('Integrity issues detected')).toBeVisible()

    await page.getByRole('button', { name: 'Preview cleanup' }).click()
    await expect(page.getByText('Integrity check results')).toBeVisible()

    await page.getByRole('button', { name: 'Jump to row' }).first().click()
    const row = page.locator('[data-application-id="app-stale-1"]')
    await expect(row).toBeVisible()
  })
})
