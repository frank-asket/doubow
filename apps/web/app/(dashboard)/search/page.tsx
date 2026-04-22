'use client'

import { Suspense, useMemo } from 'react'
import Link from 'next/link'
import type { Route } from 'next'
import { useSearchParams } from 'next/navigation'
import { Search } from 'lucide-react'

const PANELS: Array<{ label: string; href: Route; hint: string }> = [
  { label: 'Dashboard', href: '/dashboard', hint: 'Overview and monthly KPIs' },
  { label: 'Discover', href: '/discover', hint: 'Job discovery and fit scores' },
  { label: 'Pipeline', href: '/pipeline', hint: 'Application pipeline tracking' },
  { label: 'Approvals', href: '/approvals', hint: 'Approve/reject outbound drafts' },
  { label: 'Interview prep', href: '/prep', hint: 'Role-specific interview prep' },
  { label: 'My resume', href: '/resume', hint: 'Resume profile and analysis' },
  { label: 'Agents', href: '/agents', hint: 'Agent status and orchestration' },
  { label: 'Notifications', href: '/notifications', hint: 'Recent alerts' },
  { label: 'Settings', href: '/settings', hint: 'Account and dashboard settings' },
]

function SearchPageContent() {
  const params = useSearchParams()
  const query = params.get('q')?.trim() ?? ''

  const filtered = useMemo(() => {
    if (!query) return PANELS
    const needle = query.toLowerCase()
    return PANELS.filter((panel) =>
      `${panel.label} ${panel.hint}`.toLowerCase().includes(needle)
    )
  }, [query])

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <header className="flex items-center gap-3">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-indigo-700">
          <Search size={18} />
        </div>
        <div>
          <h1 className="text-[30px] font-semibold tracking-tight text-zinc-900">Search</h1>
          <p className="text-sm text-zinc-500">
            {query ? `Results for "${query}"` : 'Browse dashboard pages and tools.'}
          </p>
        </div>
      </header>

      <section className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
        {filtered.length === 0 ? (
          <p className="text-sm text-zinc-600">No results found. Try another keyword.</p>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-xl border border-zinc-100 bg-zinc-50/60 px-4 py-3 transition hover:border-indigo-200 hover:bg-indigo-50/40"
              >
                <p className="text-sm font-semibold text-zinc-900">{item.label}</p>
                <p className="text-xs text-zinc-600">{item.hint}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-5 p-5 sm:p-7">
          <div className="h-14 animate-pulse rounded-xl bg-zinc-100" />
          <div className="h-48 animate-pulse rounded-[16px] bg-zinc-100" />
        </div>
      }
    >
      <SearchPageContent />
    </Suspense>
  )
}
