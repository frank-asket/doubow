import { expect, test } from '@playwright/test'

type ViewportCase = {
  name: string
  width: number
  height: number
  expectDesktopShell: boolean
}

const CASES: ViewportCase[] = [
  { name: 'desktop-1440', width: 1440, height: 900, expectDesktopShell: true },
  { name: 'tablet-1024', width: 1024, height: 768, expectDesktopShell: true },
  { name: 'mobile-390', width: 390, height: 844, expectDesktopShell: false },
]

test.describe('dashboard visual regression', () => {
  for (const item of CASES) {
    test(`dashboard shell at ${item.name}`, async ({ page }) => {
      await page.addInitScript(() => {
        localStorage.setItem('doubow.dashboard.onboarding.v2:anon', '1')
      })
      await page.setViewportSize({ width: item.width, height: item.height })
      await page.goto('/dashboard')

      const desktopSearch = page.getByRole('textbox', { name: 'Search dashboard desktop' })
      const mobileSearch = page.getByRole('textbox', { name: 'Search dashboard mobile' })
      const dashboardNavLink = page.getByRole('link', { name: 'Overview', exact: true }).first()

      if (item.expectDesktopShell) {
        await expect(desktopSearch).toBeVisible()
        await expect(mobileSearch).toBeHidden()
      } else {
        await expect(mobileSearch).toBeVisible()
        await expect(desktopSearch).toBeHidden()
      }

      await expect(dashboardNavLink).toBeVisible()
      await page.waitForLoadState('networkidle').catch(() => {})
      await expect(page).toHaveScreenshot(`dashboard-${item.name}.png`, {
        animations: 'disabled',
        caret: 'hide',
        fullPage: false,
        // Mobile shell is more animation/layout sensitive under parallel workers.
        ...(item.name === 'mobile-390'
          ? { maxDiffPixelRatio: 0.12 }
          : {}),
      })
    })
  }
})
