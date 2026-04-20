'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import type { Route } from 'next'
import {
  LayoutDashboard, Compass, ListFilter, CheckSquare, BookOpen,
  FileText, Cpu, ChevronRight, Bell, Settings, LogOut, Menu, Search,
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
        'group flex items-center gap-2 rounded-xl border px-3 py-2 text-xs transition-all duration-150',
        active
          ? 'border-emerald-500/40 bg-emerald-500/10 font-medium text-emerald-200'
          : 'border-transparent text-zinc-400 hover:border-zinc-800 hover:bg-zinc-900/70 hover:text-zinc-200'
      )}
    >
      <Icon
        size={16}
        className={cn(active ? 'text-emerald-300' : 'text-zinc-500 group-hover:text-zinc-300')}
      />
      <span className="flex-1">{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className={cn(
            'text-2xs px-1.5 py-0.5 rounded-full font-medium tabular-nums',
            urgent ? 'bg-amber-500/15 text-amber-300' : 'bg-emerald-500/15 text-emerald-300'
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
  const path = usePathname()

  const counts: Record<string, number> = {
    jobs: summary?.high_fit_count ?? 0,
    pipeline: summary?.pipeline_count ?? 0,
    approvals: summary?.pending_approvals ?? 0,
  }

  return (
    <div className="dashboard-shell flex min-h-screen bg-black text-zinc-50">
      {/* Sidebar */}
      <aside className="hidden w-[250px] flex-shrink-0 flex-col border-r border-zinc-900 bg-[#060606] lg:flex">
        {/* Logo */}
        <div className="border-b border-zinc-900 px-5 pb-4 pt-5">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500/20 text-emerald-300">
              <ChevronRight size={16} className="text-white" strokeWidth={1.75} />
            </div>
            <span className="text-[15px] font-semibold tracking-tight text-zinc-100">Doubow</span>
          </div>
          <p className="ml-9 mt-1 text-2xs text-zinc-500">Job search AI</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-3">
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
        <div className="space-y-1 border-t border-zinc-900 p-3">
          <button className="flex w-full items-center gap-2 rounded-xl border border-transparent px-3 py-2 text-xs text-zinc-400 transition-colors hover:border-zinc-800 hover:bg-zinc-900/70 hover:text-zinc-200">
            <Bell size={16} />
            <span>Notifications</span>
          </button>
          <button className="flex w-full items-center gap-2 rounded-xl border border-transparent px-3 py-2 text-xs text-zinc-400 transition-colors hover:border-zinc-800 hover:bg-zinc-900/70 hover:text-zinc-200">
            <Settings size={16} />
            <span>Settings</span>
          </button>
          <div className="mt-1 flex items-center gap-2 px-3 py-2">
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-zinc-800 text-2xs font-medium text-zinc-100">
              FL
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-xs font-medium text-zinc-200">Franck L.</p>
              <p className="truncate text-2xs text-zinc-500">Pro</p>
            </div>
            <button className="p-0.5 text-zinc-500 hover:text-zinc-300">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="min-w-0 flex-1 bg-[#050505]">
        {/* Desktop top bar */}
        <div className="dashboard-topbar hidden h-14 items-center justify-between border-b border-zinc-900 px-6 lg:flex">
          <div>
            <p className="text-2xs text-zinc-500">Tracking / Dashboard</p>
            <p className="text-sm font-medium text-zinc-100">
              {NAV.find((i) => path === i.href || path.startsWith(i.href + '/'))?.label ?? 'Main Dashboard'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button className="btn p-2">
              <Bell size={16} />
            </button>
            <div className="relative">
              <Search size={15} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                aria-label="Search dashboard"
                className="field h-8 w-56 pl-8 pr-3 text-xs"
                placeholder="Search"
              />
            </div>
          </div>
        </div>

        {/* Mobile/tablet top nav */}
        <div className="sticky top-0 z-20 border-b border-zinc-900 bg-[#050505]/95 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500/20">
                <ChevronRight size={16} className="text-white" strokeWidth={1.75} />
              </div>
              <div>
                <p className="text-sm font-semibold text-zinc-100">Doubow</p>
                <p className="text-2xs text-zinc-500">Dashboard</p>
              </div>
            </div>
            <button className="rounded-lg border border-zinc-800 p-2 text-zinc-300 hover:bg-zinc-900/60">
              <Menu size={16} />
            </button>
          </div>
          <div className="px-3 pb-3 overflow-x-auto">
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
                      'inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs transition-colors',
                      active
                        ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                        : 'border-zinc-800 bg-zinc-900/70 text-zinc-400 hover:text-zinc-200'
                    )}
                  >
                    <Icon size={14} />
                    <span>{item.label}</span>
                    {count !== undefined && count > 0 ? (
                      <span className={cn(
                        'text-2xs px-1.5 py-0.5 rounded-full font-medium tabular-nums',
                        item.urgent ? 'bg-amber-500/15 text-amber-300' : 'bg-emerald-500/15 text-emerald-300'
                      )}>
                        {count}
                      </span>
                    ) : null}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>

        <div className="pb-8">
          {children}
        </div>
      </main>
    </div>
  )
}
