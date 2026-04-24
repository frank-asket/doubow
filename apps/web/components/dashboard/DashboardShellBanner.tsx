'use client'

/**
 * Shows when NEXT_PUBLIC_API_URL is unreachable — driven by useDashboard error.
 */
export default function DashboardShellBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="border-b border-amber-200 bg-amber-50 px-4 py-2.5 text-center text-[13px] font-semibold leading-snug text-amber-950 dark:border-amber-500/40 dark:bg-amber-500/15 dark:text-amber-50"
    >
      {message}
    </div>
  )
}
