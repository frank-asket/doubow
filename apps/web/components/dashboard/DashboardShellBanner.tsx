'use client'

/**
 * Shows when NEXT_PUBLIC_API_URL is unreachable — driven by useDashboard error.
 */
export default function DashboardShellBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="border-b border-amber-200 bg-amber-50 px-4 py-2.5 text-center text-[13px] leading-snug text-amber-950"
    >
      {message}
    </div>
  )
}
