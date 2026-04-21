'use client'

import { FormEvent, useState } from 'react'
import { usePathname } from 'next/navigation'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { Route } from 'next'
import {
  LayoutDashboard, Compass, ListFilter, CheckSquare, BookOpen,
  FileText, Cpu, Bell, Settings, LogOut, Menu, Search, ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useDashboard } from '@/hooks/useDashboard'

const NAV: Array<{ href: Route; label: string; icon: React.ElementType; badge: string | null; urgent?: boolean }> = [
  { href: '/dashboard', label: 'Dashboard',     icon: LayoutDashboard, badge: null },
  { href: '/discover',  label: 'Discover',      icon: Compass,      badge: 'jobs' },
  { href: '/pipeline',  label: 'Pipeline',       icon: ListFilter,   badge: 'pipeline' },
  { href: '/approvals', label: 'Approvals',      icon: CheckSquare,  badge: 'approvals', urgent: true },
  { href: '/prep',      label: 'Interview prep', icon: BookOpen,     badge: null },
  { href: '/resume',    label: 'My resume',      icon: FileText,     badge: null },
  { href: '/agents',    label: 'Agents',         icon: Cpu,          badge: null },
]

function NavItem({
  href, label, icon: Icon, count, urgent,
}: {
  href: Route; label: string; icon: React.ElementType; count?: number; urgent?: boolean
}) {
  const path = usePathname()
  const active = path === href || path.startsWith(href + '/')

  return (
    <Link
      href={href}
      className={cn(
        'group flex items-center gap-2.5 rounded-[10px] border px-3 py-2.5 text-[14px] transition-all duration-150',
        active
          ? 'border-[#2744cf] bg-[#1f3dbf] font-medium text-white shadow-sm'
          : 'border-transparent text-[#d7def5] hover:border-white/20 hover:bg-white/10 hover:text-white'
      )}
    >
      <Icon
        size={17}
        className={cn(active ? 'text-white' : 'text-[#d7def5] group-hover:text-white')}
      />
      <span className="flex-1">{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className={cn(
            'text-2xs px-1.5 py-0.5 rounded-full font-medium tabular-nums',
            active ? 'bg-white/20 text-white' : 'bg-white/15 text-zinc-100'
          )}
        >
          {count}
        </span>
      )}
    </Link>
  )
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { summary } = useDashboard()
  const router = useRouter()
  const path = usePathname()
  const [desktopSearch, setDesktopSearch] = useState('')
  const [mobileSearch, setMobileSearch] = useState('')

  const submitSearch = (value: string) => {
    const query = value.trim()
    if (!query) {
      router.push('/search')
      return
    }
    router.push(`/search?q=${encodeURIComponent(query)}`)
  }

  const onDesktopSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submitSearch(desktopSearch)
  }

  const onMobileSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submitSearch(mobileSearch)
  }

  const counts: Record<string, number> = {
    jobs: summary?.high_fit_count ?? 0,
    pipeline: summary?.pipeline_count ?? 0,
    approvals: summary?.pending_approvals ?? 0,
  }

  return (
    <div className="flex min-h-screen bg-[#f3f4f8] text-zinc-900">
      {/* Sidebar */}
      <aside className="hidden w-[210px] flex-shrink-0 flex-col rounded-r-2xl bg-[#020b31] text-zinc-100 lg:flex">
        {/* Logo */}
        <div className="border-b border-white/10 px-4 pb-4 pt-6">
          <div className="flex items-center gap-2">
            <span className="text-[33px] font-semibold tracking-tight text-white">Doubow.</span>
          </div>
          <p className="mt-1 text-[11px] text-[#d7def5]/85">Career Command Center</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
          {NAV.map((item) => (
            <NavItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              count={item.badge ? counts[item.badge] : undefined}
              urgent={item.urgent}
            />
          ))}
        </nav>

        {/* Footer */}
        <div className="space-y-1 border-t border-white/10 p-3">
          <Link
            href="/subscribe"
            className="mb-2 block rounded-2xl border border-white/15 bg-white px-3 py-3 text-zinc-900 shadow-sm transition hover:border-white/30"
          >
            <span className="inline-flex items-center rounded-full bg-indigo-700 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
              Doubow Pro
            </span>
            <p className="mt-2 text-[23px] font-bold leading-[1.08] tracking-tight text-indigo-900">
              Get Personal Career
              <br />
              Coach On-the-go
            </p>
            <p className="mt-1 text-[11px] leading-relaxed text-zinc-600">
              Get reach and hired easily with tips for your professional coach.
            </p>
            <span className="mt-3 inline-flex items-center gap-1 rounded-lg bg-[#FFBC01] px-2.5 py-1.5 text-[11px] font-semibold text-black">
              Upgrade to Pro
              <ChevronRight size={13} />
            </span>
          </Link>
          <Link
            href="/notifications"
            className="flex w-full items-center gap-2 rounded-[10px] border border-transparent px-3 py-2 text-[14px] text-[#d7def5] transition-colors hover:border-white/20 hover:bg-white/10 hover:text-white"
          >
            <Bell size={16} />
            <span>Notifications</span>
          </Link>
          <Link
            href="/settings"
            className="flex w-full items-center gap-2 rounded-[10px] border border-transparent px-3 py-2 text-[14px] text-[#d7def5] transition-colors hover:border-white/20 hover:bg-white/10 hover:text-white"
          >
            <Settings size={16} />
            <span>Settings</span>
          </Link>
          <div className="mt-1 flex items-center gap-2 px-3 py-2">
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-white/20 text-2xs font-medium text-white">
              FL
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-xs font-medium text-zinc-100">Franck L.</p>
              <p className="truncate text-2xs text-zinc-300">Pro</p>
            </div>
            <button className="p-0.5 text-zinc-300 hover:text-white">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="min-w-0 flex-1 bg-[#f3f4f8]">
        {/* Desktop top bar */}
        <div className="hidden h-[78px] items-center justify-between border-b border-[#e7e8ee] bg-[#f8f8fb] px-7 lg:flex">
          <form className="relative w-full max-w-md" onSubmit={onDesktopSearch}>
            <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
                aria-label="Search dashboard desktop"
              className="h-10 w-full rounded-[10px] border border-[#e1e2e9] bg-[#f8f8fb] pl-9 pr-3 text-[13px] text-zinc-700 outline-none focus:border-indigo-300"
              placeholder="Search anything here..."
              value={desktopSearch}
              onChange={(event) => setDesktopSearch(event.target.value)}
            />
          </form>
          <div className="ml-4 flex items-center gap-3">
            <Link
              href="/notifications"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#e1e2e9] text-zinc-500 hover:bg-zinc-50"
              aria-label="Open notifications"
            >
              <Bell size={16} />
            </Link>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-200 text-xs font-semibold text-zinc-700">
                FL
              </div>
              <div>
                <p className="text-sm font-medium text-zinc-800">Franck L.</p>
                <p className="text-xs text-zinc-500">
                  {NAV.find((i) => path === i.href || path.startsWith(i.href + '/'))?.label ?? 'Dashboard'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile/tablet top nav */}
        <div className="sticky top-0 z-20 border-b border-zinc-200 bg-white/95 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2">
              <div>
                <p className="text-sm font-bold text-zinc-900">Doubow.</p>
                <p className="text-2xs text-zinc-500">Dashboard</p>
              </div>
            </div>
            <button className="rounded-lg border border-zinc-300 p-2 text-zinc-600 hover:bg-zinc-100">
              <Menu size={16} />
            </button>
          </div>
          <div className="px-4 pb-3">
            <form className="relative" onSubmit={onMobileSearch}>
              <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                aria-label="Search dashboard mobile"
                className="h-10 w-full rounded-[10px] border border-[#e1e2e9] bg-[#f8f8fb] pl-9 pr-3 text-[13px] text-zinc-700 outline-none focus:border-indigo-300"
                placeholder="Search anything here..."
                value={mobileSearch}
                onChange={(event) => setMobileSearch(event.target.value)}
              />
            </form>
          </div>
          <div className="overflow-x-auto px-3 pb-3">
            <div className="flex items-center gap-1.5 min-w-max">
              {NAV.map((item) => {
                const Icon = item.icon
                const active = path === item.href || path.startsWith(item.href + '/')
                const count = item.badge ? counts[item.badge] : undefined
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-xl border px-2 py-1 text-[13px] transition-colors sm:px-2.5 sm:py-1.5',
                      active
                        ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                        : 'border-zinc-200 bg-white text-zinc-500 hover:text-zinc-700'
                    )}
                  >
                    <Icon size={14} />
                    <span>{item.label}</span>
                    {count !== undefined && count > 0 ? (
                      <span className={cn(
                        'text-2xs px-1.5 py-0.5 rounded-full font-medium tabular-nums',
                        active ? 'bg-indigo-100 text-indigo-700' : 'bg-zinc-100 text-zinc-600'
                      )}>
                        {count}
                      </span>
                    ) : null}
                  </Link>
                )
              })}
            </div>
          </div>
          <div className="px-4 pb-3">
            <Link
              href="/subscribe"
              className="block rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-zinc-900"
            >
              <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-700">Doubow Pro</p>
              <p className="mt-1 text-[13px] font-semibold leading-snug text-zinc-900">
                Upgrade for higher limits and premium prep.
              </p>
              <span className="mt-2 inline-flex items-center gap-1 text-[12px] font-semibold text-amber-900">
                Upgrade to Pro
                <ChevronRight size={13} />
              </span>
            </Link>
          </div>
        </div>

        <div className="pb-8">
          {children}
        </div>
      </main>
    </div>
  )
}
