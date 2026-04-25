import { expect, test } from '@playwright/test'

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

    await page.route('**/v1/me/resume', async (route) => {
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

    await page.route('**/v1/me/preferences', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResumeProfile.preferences),
      })
    })

    await page.route('**/v1/me/resume/analyze', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ analysis: 'Profile analysis generated for smoke test.' }),
      })
    })

    await page.addInitScript(() => {
      localStorage.setItem('doubow.dashboard.onboarding.v2:anon', '1')
    })

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

    await expect(page.getByText(/Resume uploaded\. Search preferences were updated/i)).toBeVisible()
    await expect(saveButton).toBeEnabled()

    await saveButton.click()
    await expect(page.getByText('Preferences saved.')).toBeVisible()

    await page.getByRole('button', { name: 'Analyze Core' }).click()
    await expect(page.getByText('Profile analysis generated for smoke test.')).toBeVisible()
  })

  test('discover flow: stats render from live data shape', async ({ page }) => {
    const now = new Date().toISOString()

    await page.route('**/v1/me/dashboard', async (route) => {
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

    await page.route('**/v1/jobs**', async (route) => {
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

    await page.addInitScript(() => {
      localStorage.setItem('doubow.dashboard.onboarding.v2:anon', '1')
    })

    await page.goto('/discover')
    await expect(page.getByRole('heading', { name: 'Discover' })).toBeVisible()

    await expect(page.getByText('Evaluated this week')).toBeVisible()
    await expect(page.getByText('High fit (>= 4.0)')).toBeVisible()
    await expect(page.getByText('Avg fit score')).toBeVisible()
    await expect(page.getByText('Applied')).toBeVisible()

    await expect(page.getByText('148')).toBeVisible()
    await expect(page.getByText('3.8')).toBeVisible()
    await expect(page.getByText('Top matches · 2 shown')).toBeVisible()
  })
})
