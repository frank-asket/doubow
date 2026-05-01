import { expect, test } from '@playwright/test'

import { ONBOARDING_COMPLETED_INIT } from './e2e-onboarding'
import { mockDashboardApis, mockDiscoverCatalogSupport } from './mock-dashboard-api'

/**
 * Exercises the same routes as production with Playwright network mocks (no local API process).
 * For true API integration, run the FastAPI server and use a separate run with unmocked fetches.
 */
test.describe('dashboard routes (mocked API)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(ONBOARDING_COMPLETED_INIT)
    await mockDashboardApis(page)
    await mockDiscoverCatalogSupport(page)
  })

  test('discover page renders with catalog mock', async ({ page }) => {
    await page.goto('/discover')
    await expect(page.getByRole('heading', { name: 'Job catalog', exact: true })).toBeVisible()
    await expect(page.getByText(/Top matches · \d+ in list/)).toBeVisible()
    await expect(page.getByText('Acme Labs')).toBeVisible()
  })

  test('pipeline page renders with live backend', async ({ page }) => {
    await page.goto('/pipeline')
    await expect(page.getByRole('heading', { name: 'My applications', exact: true })).toBeVisible()
  })

  test('approvals page renders with live backend', async ({ page }) => {
    await page.goto('/approvals')
    await expect(page.getByRole('heading', { name: 'Draft Approvals', exact: true })).toBeVisible()
  })

  test('assistant page renders with live backend', async ({ page }) => {
    await page.goto('/messages')
    await expect(page.getByRole('heading', { name: 'Doubow Assistant', exact: true })).toBeVisible()
  })
})
