# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/dashboard_visual.spec.ts >> dashboard visual regression >> dashboard shell at mobile-390
- Location: frontend/tests/dashboard_visual.spec.ts:18:9

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/dashboard", waiting until "load"

```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test'
  2  | 
  3  | type ViewportCase = {
  4  |   name: string
  5  |   width: number
  6  |   height: number
  7  |   expectDesktopShell: boolean
  8  | }
  9  | 
  10 | const CASES: ViewportCase[] = [
  11 |   { name: 'desktop-1440', width: 1440, height: 900, expectDesktopShell: true },
  12 |   { name: 'tablet-1024', width: 1024, height: 768, expectDesktopShell: true },
  13 |   { name: 'mobile-390', width: 390, height: 844, expectDesktopShell: false },
  14 | ]
  15 | 
  16 | test.describe('dashboard visual regression', () => {
  17 |   for (const item of CASES) {
  18 |     test(`dashboard shell at ${item.name}`, async ({ page }) => {
  19 |       await page.setViewportSize({ width: item.width, height: item.height })
> 20 |       await page.goto('/dashboard')
     |                  ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  21 | 
  22 |       const desktopSearch = page.getByRole('textbox', { name: 'Search dashboard desktop' })
  23 |       const mobileSearch = page.getByRole('textbox', { name: 'Search dashboard mobile' })
  24 |       const dashboardNavLink = page.getByRole('link', { name: 'Dashboard', exact: true }).first()
  25 | 
  26 |       if (item.expectDesktopShell) {
  27 |         await expect(desktopSearch).toBeVisible()
  28 |         await expect(mobileSearch).toBeHidden()
  29 |       } else {
  30 |         await expect(mobileSearch).toBeVisible()
  31 |         await expect(desktopSearch).toBeHidden()
  32 |       }
  33 | 
  34 |       await expect(dashboardNavLink).toBeVisible()
  35 |       await expect(page).toHaveScreenshot(`dashboard-${item.name}.png`, {
  36 |         animations: 'disabled',
  37 |         caret: 'hide',
  38 |         fullPage: false,
  39 |       })
  40 |     })
  41 |   }
  42 | })
  43 | 
```