/** Playwright smoke uses this to hit mocked APIs without a Clerk session (see playwright.config.ts). */
export function isE2EAuthBypass(): boolean {
  return process.env.NEXT_PUBLIC_E2E_BYPASS_AUTH === '1'
}
