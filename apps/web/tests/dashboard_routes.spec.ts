import { expect, test } from '@playwright/test'

import { ONBOARDING_COMPLETED_INIT } from './e2e-onboarding'
import { mockDashboardApis } from './mock-dashboard-api'

test.describe('dashboard routes smoke', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(ONBOARDING_COMPLETED_INIT)
    await mockDashboardApis(page)
  })

  test('pipeline page renders', async ({ page }) => {
    await page.goto('/pipeline')
    await expect(page.getByRole('heading', { name: 'My applications', exact: true })).toBeVisible()
  })

  test('approvals page renders', async ({ page }) => {
    await page.goto('/approvals')
    await expect(page.getByRole('heading', { name: 'Draft Approvals', exact: true })).toBeVisible()
  })

  test('interview prep page renders', async ({ page }) => {
    await page.goto('/prep')
    await expect(
      page.getByRole('heading', { name: 'Interview Preparation Hub', exact: true }),
    ).toBeVisible()
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
