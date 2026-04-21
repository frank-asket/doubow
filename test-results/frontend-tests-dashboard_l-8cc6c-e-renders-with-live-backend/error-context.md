# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/dashboard_live.spec.ts >> dashboard routes live backend >> agents page renders with live backend
- Location: frontend/tests/dashboard_live.spec.ts:20:7

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/agents", waiting until "load"

```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test'
  2  | 
  3  | test.describe('dashboard routes live backend', () => {
  4  |   test('discover page renders with live backend', async ({ page }) => {
  5  |     await page.goto('/discover')
  6  |     await expect(page.getByRole('heading', { name: 'Discover', exact: true })).toBeVisible()
  7  |     await expect(page.getByText('Evaluated this week')).toBeVisible()
  8  |   })
  9  | 
  10 |   test('pipeline page renders with live backend', async ({ page }) => {
  11 |     await page.goto('/pipeline')
  12 |     await expect(page.getByRole('heading', { name: 'Pipeline', exact: true })).toBeVisible()
  13 |   })
  14 | 
  15 |   test('approvals page renders with live backend', async ({ page }) => {
  16 |     await page.goto('/approvals')
  17 |     await expect(page.getByRole('heading', { name: 'Pending approvals', exact: true })).toBeVisible()
  18 |   })
  19 | 
  20 |   test('agents page renders with live backend', async ({ page }) => {
> 21 |     await page.goto('/agents')
     |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  22 |     await expect(page.getByRole('heading', { name: 'Agent status', exact: true })).toBeVisible()
  23 |   })
  24 | })
  25 | 
```