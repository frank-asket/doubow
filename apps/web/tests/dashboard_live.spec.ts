import { expect, test } from '@playwright/test'

test.describe('dashboard routes live backend', () => {
  test('discover page renders with live backend', async ({ page }) => {
    await page.goto('/discover')
    await expect(page.getByRole('heading', { name: 'Discover', exact: true })).toBeVisible()
    await expect(page.getByText('Evaluated this week')).toBeVisible()
  })

  test('pipeline page renders with live backend', async ({ page }) => {
    await page.goto('/pipeline')
    await expect(page.getByRole('heading', { name: 'Pipeline', exact: true })).toBeVisible()
  })

  test('approvals page renders with live backend', async ({ page }) => {
    await page.goto('/approvals')
    await expect(page.getByRole('heading', { name: 'Pending approvals', exact: true })).toBeVisible()
  })

  test('assistant page renders with live backend', async ({ page }) => {
    await page.goto('/messages')
    await expect(page.getByRole('heading', { name: 'Doubow Assistant', exact: true })).toBeVisible()
  })
})
