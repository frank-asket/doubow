/**
 * Dashboard tour uses `doubow.dashboard.onboarding.v2:${userId}`.
 * With Clerk publishable key set, unsigned E2E runs use `clerk-signed-in` (see `app/(dashboard)/layout.tsx`).
 * Without Clerk, layout uses `anon`. Set both so Playwright always skips the dialog.
 */
export const ONBOARDING_COMPLETED_INIT = () => {
  for (const id of ['anon', 'clerk-signed-in']) {
    try {
      localStorage.setItem(`doubow.dashboard.onboarding.v2:${id}`, '1')
    } catch {
      /* ignore */
    }
  }
}
