'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import { usePathname } from 'next/navigation'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { Route } from 'next'
import {
  LayoutDashboard, Compass, ListFilter, CheckSquare, BookOpen,
  FileText, Bell, Settings, LogOut, Menu, Search, ChevronRight,   HelpCircle, Sun, Moon, FileEdit,
  Sparkles,
} from 'lucide-react'
import posthog from 'posthog-js'
import { useClerk, useUser } from '@clerk/nextjs'
import { cn } from '@/lib/utils'
import { useDashboard } from '@/hooks/useDashboard'
import { planLabelFromPublicMetadata, type ClerkPlanPublicMetadata } from '@/lib/clerkPlan'
import DashboardShellBanner from '@/components/dashboard/DashboardShellBanner'
import DashboardOnboardingDialog from '@/components/dashboard/DashboardOnboardingDialog'
import ApiConnectionHealthGate from '@/components/dev/ApiConnectionHealth'

/** Aligned with docs/mockup/your_career_dashboard_guided — Candidate Hub labels */
const NAV: Array<{ href: Route; label: string; icon: React.ElementType; badge: string | null; urgent?: boolean }> = [
  { href: '/dashboard', label: 'Overview',       icon: LayoutDashboard, badge: null },
  { href: '/discover',  label: 'Job matches',    icon: Compass,         badge: 'jobs' },
  { href: '/pipeline',  label: 'Pipeline',       icon: ListFilter,      badge: 'pipeline' },
  { href: '/drafts' as Route, label: 'Drafts', icon: FileEdit, badge: null },
  { href: '/approvals', label: 'Approvals',      icon: CheckSquare,     badge: 'approvals', urgent: true },
  { href: '/messages' as Route, label: 'Assistant', icon: Sparkles, badge: null },
  { href: '/prep',      label: 'Interviews',     icon: BookOpen,        badge: null },
  { href: '/resume',    label: 'Resume',         icon: FileText,        badge: null },
]

function NavItem({
  href, label, icon: Icon, count, urgent,
}: {
  href: Route; label: string; icon: React.ElementType; count?: number; urgent?: boolean
}) {
  const path = usePathname()
  const active = path === href || path.startsWith(href + '/')
  const showUrgent = Boolean(urgent && count !== undefined && count > 0)

  return (
    <Link
      href={href}
      className={cn(
        'group motion-nav flex items-center gap-3 border-l-[3px] px-3 py-2.5 text-[14px] hover:-translate-y-[1px]',
        showUrgent && !active && 'ring-1 ring-amber-400/50 rounded-r-lg',
        active
          ? 'border-primary-green bg-white font-semibold text-primary-green shadow-sm shadow-primary-green/10 dark:bg-slate-800 dark:text-emerald-200 dark:shadow-secondary-green/15'
          : 'border-transparent font-medium text-zinc-700 hover:bg-slate-100 hover:text-primary-green hover:shadow-sm hover:shadow-slate-300/40 dark:font-medium dark:text-white dark:hover:bg-slate-800 dark:hover:text-emerald-200 dark:hover:shadow-black/30',
      )}
    >
      <Icon size={20} className={cn('motion-icon group-hover:scale-[1.06]', active ? 'text-secondary-green dark:text-emerald-200' : 'text-zinc-700 group-hover:text-secondary-green dark:font-bold dark:text-white dark:group-hover:text-emerald-200')} />
      <span className="flex-1">{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className={cn(
            'text-2xs rounded-full px-1.5 py-0.5 font-medium tabular-nums',
            active ? 'bg-bg-light-green text-primary-green dark:bg-primary-green/20 dark:text-emerald-200' : 'bg-slate-200/80 font-bold text-zinc-700 dark:bg-slate-700 dark:font-bold dark:text-white',
          )}
        >
          {count}
        </span>
      )}
    </Link>
  )
}

function userInitials(first?: string | null, last?: string | null, email?: string | null) {
  const a = first?.trim().charAt(0)
  const b = last?.trim().charAt(0)
  if (a && b) return `${a}${b}`.toUpperCase()
  if (a) return a.toUpperCase()
  const local = email?.split('@')[0]?.slice(0, 2)
  return local?.toUpperCase() ?? '?'
}

type DashboardLayoutInnerProps = {
  children: React.ReactNode
  displayName: string
  initials: string
  userLoaded: boolean
  planLabel: string
  onSignOut: () => void
  /** Stable id for onboarding localStorage (Clerk user id or `anon`) */
  onboardingUserId: string | undefined
}

function DashboardLayoutInner({
  children,
  displayName,
  initials,
  userLoaded,
  planLabel,
  onSignOut,
  onboardingUserId,
}: DashboardLayoutInnerProps) {
  const { summary, error: dashboardError } = useDashboard()
  const router = useRouter()
  const path = usePathname()
  const [desktopSearch, setDesktopSearch] = useState('')
  const [mobileSearch, setMobileSearch] = useState('')
  const [mobileNavOpen, setMobileNavOpen] = useState(true)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const preferred = typeof window !== 'undefined'
      ? window.localStorage.getItem('dashboard-theme')
      : null
    if (preferred === 'dark' || preferred === 'light') {
      setTheme(preferred)
      return
    }
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark')
    }
  }, [])

  useEffect(() => {
    if (typeof document === 'undefined') return
    document.documentElement.classList.toggle('dark', theme === 'dark')
    window.localStorage.setItem('dashboard-theme', theme)
  }, [theme])

  const apiBannerMessage =
    dashboardError != null
      ? 'Cannot reach the Doubow API. Start your backend (see README) or check NEXT_PUBLIC_API_URL.'
      : null

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
    <div className="dashboard-chrome flex min-h-screen bg-[#f5faf8] font-medium text-zinc-700 transition-colors dark:bg-slate-950 dark:text-slate-50">
      {/* Sidebar — Candidate Hub (mockup: light rail + teal active state) */}
      <aside className="hidden w-64 flex-shrink-0 flex-col border-r border-slate-200/90 bg-slate-50/95 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/90 lg:flex">
        <div className="border-b border-slate-200 px-4 pb-5 pt-6 dark:border-slate-800">
          <span className="text-xl font-black uppercase tracking-tighter text-secondary-green dark:text-emerald-400">Doubow</span>
          <div className="mt-5">
            <h2 className="text-base font-bold text-zinc-700 dark:text-white">Candidate Hub</h2>
            <div className="mt-1 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-secondary-green" aria-hidden />
              <p className="text-[11px] font-semibold uppercase tracking-wider text-zinc-700 dark:text-white">Assistant online</p>
            </div>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 py-4">
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

        <ApiConnectionHealthGate />

        <div className="mt-auto space-y-1 border-t border-slate-200 p-4">
          <Link
            href="/discover"
            className="motion-cta mb-4 flex w-full items-center justify-center rounded border border-primary-green bg-primary-green px-3 py-2 text-[14px] font-medium text-white shadow-sm hover:-translate-y-[1px] hover:brightness-110 hover:shadow-md hover:shadow-primary-green/20"
          >
            Find new jobs
          </Link>
          <Link
            href="/billing"
            className="motion-card mb-4 block rounded-2xl border border-amber-400/90 bg-gradient-to-b from-[#FFBC01] via-[#ffc21a] to-[#f0b100] px-4 py-4 text-left shadow-md shadow-amber-500/20 ring-1 ring-amber-300/60 hover:-translate-y-[2px] hover:shadow-lg hover:shadow-amber-500/25 dark:border-amber-500/55 dark:from-amber-500 dark:via-amber-500 dark:to-amber-600 dark:ring-amber-400/35"
          >
            <span className="inline-flex items-center rounded-full bg-black/12 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-zinc-950 dark:bg-black/25 dark:text-white">
              Doubow Pro
            </span>
            <p className="mt-3 text-[16px] font-bold leading-snug tracking-tight text-zinc-950 dark:text-white">
              Your personal career coach, everywhere you go.
            </p>
            <p className="mt-2 text-[12px] font-bold leading-relaxed text-zinc-700/95 dark:text-amber-50">
              Unlock higher AI limits, Gmail-ready drafts, premium interview prep, and priority support.
            </p>
            <span className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-zinc-950 px-3 py-2.5 text-[13px] font-bold text-white shadow-inner dark:bg-black">
              Upgrade to Pro
              <ChevronRight size={16} className="opacity-90" aria-hidden />
            </span>
          </Link>
          <Link
            href="/settings"
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[14px] font-bold text-zinc-700 transition-colors hover:bg-slate-100 dark:font-bold dark:text-white dark:hover:bg-slate-800"
          >
            <Settings size={18} />
            <span>Profile settings</span>
          </Link>
          <Link
            href="/search"
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[14px] font-bold text-zinc-700 transition-colors hover:bg-slate-100 dark:font-bold dark:text-white dark:hover:bg-slate-800"
          >
            <HelpCircle size={18} />
            <span>Help</span>
          </Link>
          <div className="flex items-center gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-xs font-bold text-zinc-700 dark:border-slate-700 dark:bg-slate-800 dark:font-bold dark:text-white">
              {userLoaded ? initials.slice(0, 2) : '…'}
            </div>
            <Link href="/profile" className="min-w-0 flex-1">
              <p className="truncate text-xs font-bold text-zinc-700 dark:text-white">{userLoaded ? displayName : '…'}</p>
              <p className="truncate text-2xs font-bold text-zinc-700 dark:font-bold dark:text-white">{planLabel}</p>
            </Link>
            <button
              type="button"
              title="Sign out"
              aria-label="Sign out"
              className="rounded p-1 font-bold text-zinc-700 hover:bg-slate-200 hover:text-zinc-700 dark:font-bold dark:text-white dark:hover:bg-slate-800 dark:hover:text-white"
              onClick={onSignOut}
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="min-w-0 flex-1 bg-[#f5faf8] transition-colors dark:bg-slate-950">
        {apiBannerMessage ? <DashboardShellBanner message={apiBannerMessage} /> : null}
        {/* Desktop top bar */}
        <div className="hidden h-14 items-center justify-between border-b border-slate-200 bg-white/90 px-6 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/90 lg:flex">
          <form className="relative w-full max-w-md" onSubmit={onDesktopSearch}>
            <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-700 dark:font-bold dark:text-white" />
            <input
              aria-label="Search dashboard desktop"
              className="h-9 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-[13px] font-bold text-zinc-700 outline-none focus:border-secondary-green focus:ring-1 focus:ring-secondary-green/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              placeholder="Search anything here..."
              value={desktopSearch}
              onChange={(event) => setDesktopSearch(event.target.value)}
            />
          </form>
          <nav className="ml-6 hidden flex-1 items-center justify-center gap-8 xl:flex" aria-label="Workspace">
            <Link
              href="/discover"
              className={cn(
                'border-b-2 pb-1 text-sm font-bold transition-colors dark:font-semibold',
                path === '/dashboard' || path === '/discover' || path.startsWith('/discover/')
                  ? 'border-primary-green text-primary-green dark:text-emerald-300'
                  : 'border-transparent font-bold text-zinc-700 hover:text-primary-green dark:font-bold dark:text-white dark:hover:text-white',
              )}
            >
              Jobs
            </Link>
            <Link
              href="/pipeline"
              className={cn(
                'border-b-2 pb-1 text-sm font-bold transition-colors dark:font-semibold',
                path === '/pipeline' || path.startsWith('/pipeline/')
                  ? 'border-primary-green text-primary-green dark:text-emerald-300'
                  : 'border-transparent font-bold text-zinc-700 hover:text-primary-green dark:font-bold dark:text-white dark:hover:text-white',
              )}
            >
              Applications
            </Link>
            <Link
              href={'/messages' as Route}
              className={cn(
                'border-b-2 pb-1 text-sm font-bold transition-colors dark:font-semibold',
                path === '/messages' || path.startsWith('/messages/')
                  ? 'border-primary-green text-primary-green dark:text-emerald-300'
                  : 'border-transparent font-bold text-zinc-700 hover:text-primary-green dark:font-bold dark:text-white dark:hover:text-white',
              )}
            >
              Assistant
            </Link>
            <Link
              href="/resume"
              className={cn(
                'border-b-2 pb-1 text-sm font-bold transition-colors',
                path === '/resume' || path.startsWith('/resume/')
                  ? 'border-primary-green text-primary-green dark:text-emerald-400'
                  : 'border-transparent font-bold text-zinc-700 hover:text-primary-green dark:font-bold dark:text-white dark:hover:text-white',
              )}
            >
              Resume
            </Link>
          </nav>
          <div className="ml-4 flex flex-shrink-0 items-center gap-3">
            <button
              type="button"
              onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
              className="motion-icon inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 font-bold text-zinc-700 hover:-translate-y-[1px] hover:bg-slate-50 hover:shadow-sm dark:border-slate-700 dark:font-bold dark:text-white dark:hover:bg-slate-800"
              aria-label="Toggle day and night theme"
            >
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link
              href={'/messages' as Route}
              className="motion-icon inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 font-bold text-zinc-700 hover:-translate-y-[1px] hover:bg-slate-50 hover:shadow-sm dark:border-slate-700 dark:font-bold dark:text-white dark:hover:bg-slate-800"
              aria-label="Open Assistant"
            >
              <Bell size={16} />
            </Link>
            <Link
              href="/search"
              className="motion-icon inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 font-bold text-zinc-700 hover:-translate-y-[1px] hover:bg-slate-50 hover:shadow-sm dark:border-slate-700 dark:font-bold dark:text-white dark:hover:bg-slate-800"
              aria-label="Help"
            >
              <HelpCircle size={16} />
            </Link>
            <div className="flex items-center gap-2 border-l border-slate-200 pl-3 dark:border-slate-700">
              <div className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-slate-100 text-xs font-bold text-zinc-700 dark:border-slate-700 dark:bg-slate-800 dark:font-bold dark:text-white">
                {userLoaded ? initials : '…'}
              </div>
              <Link href="/profile" className="hidden min-w-0 sm:block">
                <p className="truncate text-sm font-bold text-zinc-700 dark:text-white">{userLoaded ? displayName : '…'}</p>
                <p className="truncate text-xs font-bold text-zinc-700 dark:font-bold dark:text-white">
                  {NAV.find((i) => path === i.href || path.startsWith(i.href + '/'))?.label ?? 'Overview'}
                </p>
              </Link>
            </div>
            <Link
              href="/discover"
              className="motion-cta hidden rounded border border-primary-green bg-primary-green px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:-translate-y-[1px] hover:brightness-110 hover:shadow-md hover:shadow-primary-green/20 md:inline-flex"
            >
              Apply now
            </Link>
          </div>
        </div>

        {/* Mobile/tablet top nav */}
        <div className="sticky top-0 z-20 border-b border-zinc-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95 lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2">
              <div>
                <p className="text-sm font-black uppercase tracking-tighter text-secondary-green dark:text-emerald-400">Doubow</p>
                <p className="text-2xs font-bold text-zinc-700 dark:font-bold dark:text-white">Candidate Hub</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
                className="motion-icon rounded-lg border border-zinc-300 p-2 font-bold text-zinc-700 hover:-translate-y-[1px] hover:bg-zinc-100 hover:shadow-sm dark:border-slate-700 dark:font-bold dark:text-white dark:hover:bg-slate-800"
                aria-label="Toggle day and night theme"
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </button>
              <button
                type="button"
                aria-expanded={mobileNavOpen}
                aria-label={mobileNavOpen ? 'Collapse navigation' : 'Expand navigation'}
                className="motion-icon rounded-lg border border-zinc-300 p-2 font-bold text-zinc-700 hover:-translate-y-[1px] hover:bg-zinc-100 hover:shadow-sm dark:border-slate-700 dark:font-bold dark:text-white dark:hover:bg-slate-800"
                onClick={() => setMobileNavOpen((o) => !o)}
              >
                <Menu size={16} />
              </button>
            </div>
          </div>
          {mobileNavOpen ? (
            <>
          <div className="px-4 pb-3">
            <form className="relative" onSubmit={onMobileSearch}>
              <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-700 dark:font-bold dark:text-white" />
              <input
                aria-label="Search dashboard mobile"
                className="h-10 w-full rounded-[10px] border border-zinc-200 bg-white pl-9 pr-3 text-[13px] font-bold text-zinc-700 outline-none focus:border-secondary-green focus:ring-1 focus:ring-secondary-green/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
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
                      'motion-nav inline-flex items-center gap-1.5 rounded-xl border px-2 py-1 text-[13px] hover:-translate-y-[1px] sm:px-2.5 sm:py-1.5',
                      active
                        ? 'border-secondary-green/30 bg-bg-light-green text-primary-green dark:border-secondary-green/40 dark:bg-primary-green/20 dark:text-emerald-200'
                        : 'border-zinc-200 bg-white font-bold text-zinc-700 hover:text-primary-green dark:border-slate-700 dark:bg-slate-800 dark:font-bold dark:text-white dark:hover:text-white'
                    )}
                  >
                    <Icon size={14} />
                    <span>{item.label}</span>
                    {count !== undefined && count > 0 ? (
                      <span className={cn(
                        'text-2xs px-1.5 py-0.5 rounded-full font-medium tabular-nums',
                        active ? 'bg-highlight-green text-primary-green dark:bg-primary-green/30 dark:text-emerald-200' : 'bg-zinc-100 font-bold text-zinc-700 dark:bg-slate-700 dark:font-bold dark:text-white'
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
              href="/billing"
              className="motion-card mb-2 block rounded-2xl border border-secondary-green/20 bg-white px-3 py-3 text-zinc-700 shadow-sm ring-1 ring-secondary-green/15 hover:-translate-y-[1px] hover:border-secondary-green/30 hover:shadow-md hover:shadow-primary-green/10 dark:border-secondary-green/30 dark:bg-slate-900 dark:text-slate-100 dark:ring-secondary-green/25 dark:hover:border-emerald-400/50"
            >
              <span className="inline-flex items-center rounded-full bg-primary-green px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                Doubow Pro
              </span>
              <p className="mt-2 text-[15px] font-bold leading-snug tracking-tight text-primary-green dark:text-emerald-100">
                Get Personal Career Coach On-the-go
              </p>
              <p className="mt-1 text-[11px] font-bold leading-relaxed text-zinc-700 dark:font-bold dark:text-white">
                Higher limits, Gmail drafts, and premium prep when you upgrade.
              </p>
              <span className="mt-3 inline-flex items-center gap-1 rounded-lg bg-[#FFBC01] px-2.5 py-1.5 text-[11px] font-semibold text-black">
                Upgrade to Pro
                <ChevronRight size={13} />
              </span>
            </Link>
          </div>
          <div className="space-y-1 border-t border-zinc-200 px-4 pb-4 pt-3 dark:border-slate-800">
            <Link
              href="/settings"
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-bold text-zinc-700 transition-colors hover:bg-zinc-100 dark:font-bold dark:text-white dark:hover:bg-slate-800"
            >
              <Settings size={18} />
              <span>Profile settings</span>
            </Link>
            <Link
              href="/search"
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-bold text-zinc-700 transition-colors hover:bg-zinc-100 dark:font-bold dark:text-white dark:hover:bg-slate-800"
            >
              <HelpCircle size={18} />
              <span>Help</span>
            </Link>
            <div className="flex items-center gap-2 border-t border-zinc-200 pt-3 dark:border-slate-800">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-zinc-200 bg-white text-xs font-bold text-zinc-700 dark:border-slate-700 dark:bg-slate-800 dark:font-bold dark:text-white">
                {userLoaded ? initials.slice(0, 2) : '…'}
              </div>
              <Link href="/profile" className="min-w-0 flex-1 py-0.5">
                <p className="truncate text-sm font-bold text-zinc-700 dark:text-white">{userLoaded ? displayName : '…'}</p>
                <p className="truncate text-2xs font-bold text-zinc-600 dark:font-bold dark:text-slate-300">{planLabel}</p>
              </Link>
              <button
                type="button"
                title="Sign out"
                aria-label="Sign out"
                className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg border border-zinc-200 font-bold text-zinc-700 hover:bg-zinc-100 dark:border-slate-700 dark:font-bold dark:text-white dark:hover:bg-slate-800 dark:hover:text-white"
                onClick={onSignOut}
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
            </>
          ) : null}
        </div>

        <div className="app-route-shell pb-8">
          {children}
        </div>
      </main>

      <DashboardOnboardingDialog onboardingUserId={onboardingUserId} />
    </div>
  )
}

function DashboardLayoutWithClerk({ children }: { children: React.ReactNode }) {
  const { user, isLoaded: userLoaded } = useUser()
  const { signOut } = useClerk()

  const displayName = useMemo(() => {
    if (!userLoaded || !user) return 'Account'
    const full = [user.firstName, user.lastName].filter(Boolean).join(' ')
    if (full.trim()) return full.trim()
    return user.primaryEmailAddress?.emailAddress ?? 'Account'
  }, [user, userLoaded])

  const initials = useMemo(
    () => userInitials(user?.firstName, user?.lastName, user?.primaryEmailAddress?.emailAddress),
    [user],
  )

  const planLabel = useMemo(() => {
    const meta = user?.publicMetadata as ClerkPlanPublicMetadata | undefined
    return planLabelFromPublicMetadata(meta)
  }, [user])

  const onboardingUserId = useMemo(() => {
    if (!userLoaded) return undefined
    return user?.id ?? 'clerk-signed-in'
  }, [userLoaded, user?.id])

  return (
    <DashboardLayoutInner
      displayName={displayName}
      initials={initials}
      userLoaded={userLoaded}
      planLabel={planLabel}
      onSignOut={() => {
        if (process.env.NEXT_PUBLIC_POSTHOG_KEY) {
          try {
            posthog.reset()
          } catch {
            /* ignore */
          }
        }
        void signOut({ redirectUrl: '/' })
      }}
      onboardingUserId={onboardingUserId}
    >
      {children}
    </DashboardLayoutInner>
  )
}

function DashboardLayoutWithoutClerk({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  return (
    <DashboardLayoutInner
      displayName="Account"
      initials="?"
      userLoaded
      planLabel="Free"
      onSignOut={() => router.push('/')}
      onboardingUserId="anon"
    >
      {children}
    </DashboardLayoutInner>
  )
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const hasClerk = Boolean(
    typeof process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY === 'string' &&
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.length > 0,
  )
  if (hasClerk) {
    return <DashboardLayoutWithClerk>{children}</DashboardLayoutWithClerk>
  }
  return <DashboardLayoutWithoutClerk>{children}</DashboardLayoutWithoutClerk>
}
