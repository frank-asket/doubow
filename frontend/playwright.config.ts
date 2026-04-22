import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3100'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  webServer: {
    command:
      'E2E_BYPASS_AUTH=1 NEXT_PUBLIC_E2E_BYPASS_AUTH=1 NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run build && E2E_BYPASS_AUTH=1 NEXT_PUBLIC_E2E_BYPASS_AUTH=1 NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run start -- --port 3100',
    cwd: __dirname,
    url: BASE_URL,
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
