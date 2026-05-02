'use client'

/**
 * Shows when NEXT_PUBLIC_API_URL is unreachable — driven by useDashboard error.
 */
export default function DashboardShellBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="border-b border-border-subtle bg-bg-light-orange px-4 py-2.5 text-center text-[13px] font-semibold leading-snug text-primary-orange"
    >
      {message}
    </div>
  )
}
