'use client'

import { useEffect } from 'react'

export default function ApprovalsRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Approvals route error boundary triggered', {
      message: error.message,
      digest: error.digest,
    })
  }, [error])

  return (
    <div className="approvals-surface min-h-screen bg-[#f5faf8] text-[#171d1c] dark:bg-slate-950 dark:text-slate-100">
      <main className="flex min-h-screen flex-col">
        <section className="border-b border-[#d9e1dd] bg-white/75 px-6 py-5 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/65">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#00685f] dark:text-teal-300">Approvals Workspace</p>
          <h1 className="mt-2 text-xl font-bold tracking-tight text-slate-900 dark:text-white">Draft Approvals</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            The approvals panel hit a temporary rendering issue.
          </p>
          <button
            type="button"
            onClick={reset}
            className="mt-3 rounded-[2px] bg-[#00685f] px-3 py-1.5 text-xs font-semibold text-white"
          >
            Retry loading approvals
          </button>
        </section>
      </main>
    </div>
  )
}
