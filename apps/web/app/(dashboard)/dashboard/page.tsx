'use client'

import {
  AlertTriangle,
  BarChart3,
  Bookmark,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  Coffee,
  Compass,
  Eye,
  Factory,
  FileText,
  Gauge,
  Layers,
  Lightbulb,
  BookOpen,
  Rocket,
  Search as SearchIcon,
  Sparkles,
  TrendingUp,
  Video,
  Zap,
  DollarSign,
  SlidersHorizontal,
  Hexagon,
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import useSWR from 'swr'
import { useAuth } from '@clerk/nextjs'
import { formatApplicationStatus } from '@/components/dashboard/dashboardCopy'
import { useDashboard } from '@/hooks/useDashboard'
import { applicationsApi } from '@/lib/api'
import { isE2EAuthBypass } from '@/lib/e2e'
import { candidateTokens as tk, candidatePageShell } from '@/lib/candidateUi'
import { cn, relativeTime } from '@/lib/utils'
import type { Application } from '@doubow/shared'

function sortApplicationsRecent(items: Application[]) {
  return [...items].sort(
    (a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime(),
  )
}

function fitPercent(score?: { fit_score?: number }) {
  const raw = score?.fit_score
  if (raw == null || Number.isNaN(raw)) return null
  return Math.min(100, Math.round((raw / 5) * 100))
}

export default function DashboardOverviewPage() {
  const router = useRouter()
  const { summary, loading: summaryLoading, error: summaryError } = useDashboard()
  const { isLoaded, isSignedIn } = useAuth()
  const ready = isE2EAuthBypass() || (isLoaded && isSignedIn)

  const [period, setPeriod] = useState<'month' | 'all'>('month')
  const [discoverQuery, setDiscoverQuery] = useState('')

  const { data: allApplications, error: appsError, isLoading: appsLoading } = useSWR(
    ready ? 'dashboard-overview-applications' : null,
    async () => {
      const res = await applicationsApi.list()
      return res.items
    },
    { shouldRetryOnError: false, errorRetryCount: 0 },
  )

  const recentApplications = allApplications ? sortApplicationsRecent(allApplications).slice(0, 5) : []
  const interviewApps = allApplications
    ? sortApplicationsRecent(allApplications.filter((a) => a.status === 'interview'))
    : []

  const topMatches = useMemo(() => {
    if (!allApplications?.length) return []
    return [...allApplications]
      .sort((a, b) => (b.score?.fit_score ?? 0) - (a.score?.fit_score ?? 0))
      .slice(0, 5)
  }, [allApplications])

  const recentCompanies = useMemo(() => {
    if (!allApplications?.length) return []
    const seen = new Set<string>()
    const out: string[] = []
    for (const a of sortApplicationsRecent(allApplications)) {
      const c = a.job.company?.trim()
      if (!c || seen.has(c)) continue
      seen.add(c)
      out.push(c)
      if (out.length >= 6) break
    }
    return out
  }, [allApplications])

  const pipelineCount = summary?.pipeline_count ?? 0
  const pendingApprovals = summary?.pending_approvals ?? 0
  const highFit = summary?.high_fit_count ?? 0
  const evaluatedWeek = summary?.evaluated_this_week ?? 0
  const avgFit = summary?.avg_fit_score
  const scoredTotal = summary?.total_scored_jobs ?? 0
  const profileViewsMetric = summary?.profile_views
  const showProfileViews = profileViewsMetric != null
  const responseRatePct = summary?.response_rate_pct ?? null

  const interviewCount = interviewApps.length
  const nextInterview = interviewApps[0]
  const secondInterview = interviewApps[1]

  const avgFitPct = avgFit != null ? Math.round((avgFit / 5) * 100) : null
  const resumeScoreDisplay = avgFitPct != null ? Math.min(99, Math.round(60 + avgFitPct * 0.35)) : null
  const interviewRatePct = pipelineCount > 0 ? Math.round((interviewCount / pipelineCount) * 100) : null
  const highFitRatePct = scoredTotal > 0 ? Math.round((highFit / scoredTotal) * 100) : null

  function onDiscoverSearch(e: React.FormEvent) {
    e.preventDefault()
    const q = discoverQuery.trim()
    router.push(q ? `/discover?q=${encodeURIComponent(q)}` : '/discover')
  }

  const jobCardIcon = [Building2, Sparkles, Rocket]
  const companyGridIcons = [Building2, Hexagon, Layers, Factory, Sparkles, Bookmark] as const

  return (
    <div className={candidatePageShell}>
      {/* Header — docs/mockup/your_career_dashboard_guided */}
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1
            className="text-xl font-medium tracking-tight sm:text-[20px] sm:leading-7"
            style={{ color: tk.onSurface }}
          >
            Candidate Overview
          </h1>
          <p className="mt-1 max-w-xl text-[13px] leading-snug" style={{ color: tk.onVariant }}>
            Analytical performance and application tracking.
            {period === 'all'
              ? ' Showing all-time workspace totals.'
              : ' Showing your current workspace snapshot.'}
          </p>
        </div>
        <div
          className="flex items-center gap-3 rounded border border-[0.5px] p-1 shadow-sm"
          style={{ backgroundColor: tk.surfaceLow, borderColor: tk.outline }}
        >
          <button
            type="button"
            onClick={() => setPeriod('month')}
            className={cn(
              'rounded px-4 py-1.5 text-[12px] font-medium transition-colors',
              period === 'month'
                ? 'border-[0.5px] bg-white shadow-sm dark:bg-slate-900'
                : 'text-zinc-500 hover:bg-white/60 dark:hover:bg-slate-800/60',
            )}
            style={
              period === 'month'
                ? { borderColor: tk.outline, color: tk.onSurface }
                : { color: tk.onVariant }
            }
          >
            This Month
          </button>
          <button
            type="button"
            onClick={() => setPeriod('all')}
            className={cn(
              'rounded px-4 py-1.5 text-[12px] font-medium transition-colors',
              period === 'all'
                ? 'border-[0.5px] bg-white shadow-sm dark:bg-slate-900'
                : 'text-zinc-500 hover:bg-white/60 dark:hover:bg-slate-800/60',
            )}
            style={
              period === 'all'
                ? { borderColor: tk.outline, color: tk.onSurface }
                : { color: tk.onVariant }
            }
          >
            All Time
          </button>
        </div>
      </header>

      {summaryError ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] text-amber-950">
          Dashboard stats couldn&apos;t load. Check that the backend is running and NEXT_PUBLIC_API_URL is
          correct.
        </div>
      ) : null}

      {/* Stats grid — matches guided mockup 4-up */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div
          className="flex flex-col border-[0.5px] bg-white p-4 dark:bg-slate-900"
          style={{ borderColor: 'rgba(109,122,119,0.45)' }}
        >
          <span
            className="text-[11px] font-normal uppercase tracking-tight"
            style={{ color: tk.onVariant }}
          >
            Active applications
          </span>
          <span className="mt-1 text-3xl font-black tabular-nums" style={{ color: tk.onSurface }}>
            {summaryLoading ? '…' : pipelineCount}
          </span>
          <div className="mt-auto flex items-center gap-1 pt-2 text-teal-600">
            <TrendingUp size={14} aria-hidden />
            <span className="text-xs font-bold">
              {evaluatedWeek > 0 ? `+${evaluatedWeek} this week` : 'Queue roles from Discover'}
            </span>
          </div>
        </div>

        <div
          className="flex flex-col border-[0.5px] bg-white p-4 dark:bg-slate-900"
          style={{ borderColor: 'rgba(109,122,119,0.45)' }}
        >
          <span
            className="text-[11px] font-normal uppercase tracking-tight"
            style={{ color: tk.onVariant }}
          >
            {showProfileViews ? 'Profile views' : 'Discover coverage'}
          </span>
          <span className="mt-1 text-3xl font-black tabular-nums" style={{ color: tk.onSurface }}>
            {summaryLoading ? '…' : showProfileViews ? profileViewsMetric : scoredTotal}
          </span>
          <div className="mt-auto flex items-center gap-1 pt-2 text-teal-600">
            <Eye size={14} aria-hidden />
            <span className="text-xs font-bold">
              {showProfileViews ? (
                <>
                  {profileViewsMetric === 0
                    ? 'Impressions when employers view your profile'
                    : profileViewsMetric < 100
                      ? 'Growing visibility'
                      : 'Top tier vs peer candidates'}
                </>
              ) : (
                <>
                  {highFit > 0
                    ? `${highFit} high-fit ready`
                    : avgFit != null && avgFit >= 4
                      ? 'Strong fit signal'
                      : 'Discover & score matches'}
                </>
              )}
            </span>
          </div>
        </div>

        <div
          className="flex flex-col border-[0.5px] border-l-2 bg-white p-4 dark:bg-slate-900"
          style={{ borderColor: 'rgba(109,122,119,0.45)', borderLeftColor: tk.primary }}
        >
          <span
            className="text-[11px] font-normal uppercase tracking-tight"
            style={{ color: tk.onVariant }}
          >
            Interviews scheduled
          </span>
          <span className="mt-1 text-3xl font-black tabular-nums" style={{ color: tk.onSurface }}>
            {summaryLoading ? '…' : interviewCount}
          </span>
          <div className="mt-auto flex items-center gap-1 pt-2" style={{ color: tk.primary }}>
            <CalendarDays size={14} aria-hidden />
            <span className="text-xs font-bold">
              {nextInterview ? `${nextInterview.job.company} · next in pipeline` : 'Move a role to interview'}
            </span>
          </div>
        </div>

        <div
          className="flex flex-col border-[0.5px] bg-white p-4 dark:bg-slate-900"
          style={{ borderColor: 'rgba(109,122,119,0.45)' }}
        >
          <span
            className="text-[11px] font-normal uppercase tracking-tight"
            style={{ color: tk.onVariant }}
          >
            Response rate
          </span>
          <span className="mt-1 text-3xl font-black tabular-nums" style={{ color: tk.onSurface }}>
            {summaryLoading ? '…' : responseRatePct != null ? `${responseRatePct}%` : '—'}
          </span>
          <div className="mt-auto flex items-center gap-1 pt-2" style={{ color: tk.secondary }}>
            <Gauge size={14} aria-hidden />
            <span className="text-xs font-bold">
              {responseRatePct == null
                ? 'Apply to roles to measure replies'
                : responseRatePct >= 40
                  ? 'Above average'
                  : 'Keep following up'}
            </span>
          </div>
        </div>
      </section>

      <section
        className="grid grid-cols-1 gap-3 rounded-[12px] border border-[0.5px] bg-white p-3 dark:bg-slate-900 sm:grid-cols-3"
        style={{ borderColor: tk.outline }}
      >
        <article>
          <p className="text-2xs uppercase tracking-wider" style={{ color: tk.onVariant }}>
            Interview conversion
          </p>
          <p className="mt-1 text-base font-semibold tabular-nums" style={{ color: tk.onSurface }}>
            {interviewRatePct != null ? `${interviewRatePct}%` : '—'}
          </p>
          <p className="text-2xs" style={{ color: tk.onVariant }}>
            interviews / active pipeline
          </p>
        </article>
        <article>
          <p className="text-2xs uppercase tracking-wider" style={{ color: tk.onVariant }}>
            High-fit coverage
          </p>
          <p className="mt-1 text-base font-semibold tabular-nums" style={{ color: tk.onSurface }}>
            {highFitRatePct != null ? `${highFitRatePct}%` : '—'}
          </p>
          <p className="text-2xs" style={{ color: tk.onVariant }}>
            high-fit / scored roles
          </p>
        </article>
        <article>
          <p className="text-2xs uppercase tracking-wider" style={{ color: tk.onVariant }}>
            Weekly velocity
          </p>
          <p className="mt-1 text-base font-semibold tabular-nums" style={{ color: tk.onSurface }}>
            +{evaluatedWeek}
          </p>
          <p className="text-2xs" style={{ color: tk.onVariant }}>
            roles evaluated this week
          </p>
        </article>
      </section>

      {/* Quick workspace strip — compact nav (mock sidebar “Find New Jobs” + links) */}
      <section
        aria-label="Workspace shortcuts"
        className="flex flex-col gap-3 rounded-sm border-[0.5px] bg-white p-3 dark:bg-slate-900 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4"
        style={{ borderColor: 'rgba(109,122,119,0.45)' }}
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: tk.onVariant }}>
            Workspace
          </span>
          <Link
            href="/discover"
            className="inline-flex items-center rounded border-[0.5px] px-4 py-2 text-[12px] font-semibold text-white shadow-sm transition-opacity hover:opacity-95"
            style={{ backgroundColor: tk.primary, borderColor: tk.primary }}
          >
            Find new roles
          </Link>
        </div>
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[13px] font-medium">
          {(
            [
              { href: '/discover' as const, label: 'Discover', Icon: Compass },
              { href: '/pipeline' as const, label: 'Pipeline', Icon: Briefcase },
              { href: '/approvals' as const, label: 'Approvals', Icon: ClipboardList },
              { href: '/prep' as const, label: 'Prep', Icon: BookOpen },
              { href: '/resume' as const, label: 'Resume', Icon: FileText },
              { href: '/messages' as const, label: 'Assistant', Icon: Sparkles },
            ] as const
          ).map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className="inline-flex items-center gap-1.5 transition-colors hover:underline"
              style={{ color: tk.onSurface }}
            >
              <Icon size={14} style={{ color: tk.primary }} aria-hidden />
              {label}
            </Link>
          ))}
        </nav>
      </section>

      {/* Bento */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-8">
          {/* Search & filters */}
          <div className="space-y-4 border-[0.5px] bg-white p-4 dark:bg-slate-900" style={{ borderColor: tk.outline }}>
            <form onSubmit={onDiscoverSearch} className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
              <div className="relative min-w-0 flex-1">
                <SearchIcon
                  size={20}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2"
                  style={{ color: tk.onVariant }}
                  aria-hidden
                />
                <input
                  value={discoverQuery}
                  onChange={(e) => setDiscoverQuery(e.target.value)}
                  className="w-full border-[0.5px] py-2 pl-10 pr-4 text-[13px] outline-none ring-0 focus:border-[#00685f]"
                  style={{
                    backgroundColor: tk.surfaceLow,
                    borderColor: tk.outline,
                    color: tk.onSurface,
                  }}
                  placeholder="Search roles, companies, or keywords..."
                  aria-label="Search jobs"
                />
              </div>
              <button
                type="submit"
                className="shrink-0 rounded border-[0.5px] px-6 py-2 text-[12px] font-medium text-white shadow-sm transition-opacity hover:opacity-95"
                style={{ backgroundColor: tk.primary, borderColor: tk.primary }}
              >
                Search
              </button>
            </form>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="mr-2 text-[12px] font-medium" style={{ color: tk.onVariant }}>
                  Quick filters:
                </span>
                <div className="group relative">
                  <Link
                    href="/discover?q=remote"
                    className="inline-flex items-center gap-1 rounded-full border-[0.5px] px-3 py-1 text-[12px] font-medium"
                    style={{
                      backgroundColor: tk.primaryFixed,
                      borderColor: tk.primary,
                      color: tk.onPrimaryFixedVariant,
                    }}
                  >
                    Remote-first
                  </Link>
                  <div className="pointer-events-none absolute bottom-full left-0 z-50 mb-3 w-72 rounded border-[0.5px] p-4 opacity-0 shadow-sm transition-opacity group-hover:opacity-100" style={{ backgroundColor: tk.primary, borderColor: tk.outline, color: '#f4fffc' }}>
                    <div className="absolute -bottom-1.5 left-6 h-3 w-3 rotate-45 border-b-[0.5px] border-r-[0.5px]" style={{ backgroundColor: tk.primary, borderColor: tk.outline }} />
                    <div className="flex gap-2">
                      <Lightbulb size={18} className="shrink-0" aria-hidden />
                      <div>
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-wider">Pro tip</p>
                        <p className="text-[12px] leading-tight opacity-95">
                          Narrow remote roles by adding time-zone hints (e.g. &quot;EST&quot;) in Discover search.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <Link
                  href="/discover?q=full-time"
                  className="rounded-full border-[0.5px] px-3 py-1 text-[12px] font-medium"
                  style={{
                    backgroundColor: tk.surfaceHigh,
                    borderColor: tk.outline,
                    color: tk.onVariant,
                  }}
                >
                  Full-time
                </Link>
                <Link
                  href="/discover?q=120k"
                  className="rounded-full border-[0.5px] px-3 py-1 text-[12px] font-medium"
                  style={{
                    backgroundColor: tk.surfaceHigh,
                    borderColor: tk.outline,
                    color: tk.onVariant,
                  }}
                >
                  Salary $120k+
                </Link>
                <Link
                  href="/discover?q=senior"
                  className="rounded-full border-[0.5px] px-3 py-1 text-[12px] font-medium"
                  style={{
                    backgroundColor: tk.surfaceHigh,
                    borderColor: tk.outline,
                    color: tk.onVariant,
                  }}
                >
                  Senior level
                </Link>
              </div>
              <Link
                href="/discover"
                className="inline-flex items-center gap-1 text-[12px] font-medium hover:underline"
                style={{ color: tk.primary }}
              >
                <SlidersHorizontal size={14} aria-hidden />
                All filters
              </Link>
            </div>
          </div>

          {/* Top matches — mock job listing row + meta */}
          <div className="space-y-3">
            <h3 className="px-1 text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: tk.onVariant }}>
              Top matches for you
            </h3>
            {appsError ? (
              <p className="text-sm text-rose-600">Could not load applications.</p>
            ) : appsLoading ? (
              <p className="text-sm text-zinc-500">Loading…</p>
            ) : topMatches.length === 0 ? (
              <div
                className="border-[0.5px] border-dashed bg-white/90 px-4 py-8 text-center text-sm dark:bg-slate-900/90 dark:text-slate-300"
                style={{ borderColor: 'rgba(109,122,119,0.45)', color: tk.onVariant }}
              >
                No scored matches yet.{' '}
                <Link href="/discover" className="font-semibold hover:underline" style={{ color: tk.primary }}>
                  Discover roles
                </Link>{' '}
                to build your queue.
              </div>
            ) : (
              topMatches.map((item, i) => {
                const Icon = jobCardIcon[i % jobCardIcon.length]
                const pct = fitPercent(item.score ?? undefined)
                const postedAt = item.job.posted_at ?? item.job.discovered_at
                return (
                  <Link
                    key={item.id}
                    href="/pipeline"
                    className="group block border-[0.5px] bg-white p-4 transition-colors hover:border-[#00685f] dark:bg-slate-900 dark:hover:border-teal-400"
                    style={{ borderColor: 'rgba(109,122,119,0.45)' }}
                  >
                    <div className="flex gap-4">
                      <div
                        className="flex h-12 w-12 shrink-0 items-center justify-center border-[0.5px] bg-slate-100"
                        style={{ borderColor: 'rgba(109,122,119,0.45)' }}
                      >
                        <Icon size={22} className="text-slate-400" aria-hidden />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <h4
                              className="text-[15px] font-semibold tracking-tight transition-colors group-hover:text-[#00685f]"
                              style={{ color: tk.onSurface }}
                            >
                              {item.job.title}
                            </h4>
                            <p className="text-[12px] font-medium uppercase tracking-tight" style={{ color: tk.secondary }}>
                              {item.job.company} · {item.job.location || 'Location TBD'}
                            </p>
                          </div>
                          <span className="shrink-0 text-[10px] font-medium uppercase tracking-wider tabular-nums" style={{ color: tk.onVariant }}>
                            {formatApplicationStatus(item.status)} · {relativeTime(item.last_updated)}
                          </span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-[12px]" style={{ color: tk.onVariant }}>
                          {item.job.salary_range ? (
                            <span className="inline-flex items-center gap-1">
                              <DollarSign size={18} strokeWidth={1.75} aria-hidden />
                              {item.job.salary_range}
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 opacity-70">
                              <Briefcase size={18} aria-hidden />
                              Role details in pipeline
                            </span>
                          )}
                          <span className="inline-flex items-center gap-1">
                            <Clock size={18} aria-hidden />
                            Posted {postedAt ? relativeTime(postedAt) : 'recently'}
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <Zap size={18} aria-hidden />
                            {pct != null ? `${pct}% match` : 'Score pending'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                )
              })
            )}
          </div>
        </div>

        {/* Sidebar column — guided mock: action banner + upcoming + insights + resume */}
        <div className="space-y-6 lg:col-span-4">
          {pendingApprovals > 0 ? (
            <div
              className="border-[0.5px] border-l-[3px] bg-white p-4 dark:bg-slate-900"
              style={{ borderColor: 'rgba(109,122,119,0.45)', borderLeftColor: tk.amber }}
            >
              <div className="flex gap-3">
                <AlertTriangle className="shrink-0" style={{ color: tk.amber }} size={22} aria-hidden />
                <div>
                  <h4 className="text-[13px] font-bold" style={{ color: tk.onSurface }}>
                    Action required
                  </h4>
                  <p className="mt-1 text-[13px] leading-snug" style={{ color: tk.onVariant }}>
                    You have {pendingApprovals} draft{pendingApprovals === 1 ? '' : 's'} waiting for approval before
                    send.
                  </p>
                  <Link
                    href="/approvals"
                    className="mt-3 inline-block text-[12px] font-semibold hover:underline"
                    style={{ color: tk.primary }}
                  >
                    Review approvals
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            <div
              className="border-[0.5px] bg-white p-4 dark:bg-slate-900"
              style={{ borderColor: 'rgba(109,122,119,0.45)' }}
            >
              <div className="flex gap-3">
                <CheckCircle2 className="shrink-0 text-teal-600" size={22} aria-hidden />
                <div>
                  <h4 className="text-[13px] font-bold" style={{ color: tk.onSurface }}>
                    No pending actions
                  </h4>
                  <p className="mt-1 text-[13px] leading-snug" style={{ color: tk.onVariant }}>
                    Drafts and outreach approvals will surface here when they need your attention.
                  </p>
                  <Link
                    href="/approvals"
                    className="mt-3 inline-block text-[12px] font-semibold hover:underline"
                    style={{ color: tk.primary }}
                  >
                    Open approvals queue
                  </Link>
                </div>
              </div>
            </div>
          )}

          <div className="border-[0.5px] bg-white p-5 dark:bg-slate-900" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-[12px] font-medium uppercase tracking-widest" style={{ color: tk.onVariant }}>
                Upcoming
              </h3>
              <Link href="/prep" className="text-[11px] font-bold uppercase tracking-wider" style={{ color: tk.primary }}>
                View all
              </Link>
            </div>
            {interviewApps.length === 0 ? (
              <p className="text-[13px]" style={{ color: tk.onVariant }}>
                No interview-stage applications yet. Update stages in{' '}
                <Link href="/pipeline" className="font-semibold hover:underline" style={{ color: tk.primary }}>
                  Pipeline
                </Link>
                .
              </p>
            ) : (
              <div className="space-y-4">
                {nextInterview ? (
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
                      style={{ backgroundColor: '#f0dbff', color: '#6800b4' }}
                    >
                      <Video size={18} aria-hidden />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-bold" style={{ color: tk.onSurface }}>
                        {nextInterview.job.company}
                      </p>
                      <p className="text-xs" style={{ color: tk.onVariant }}>
                        {nextInterview.job.title} · interview stage
                      </p>
                    </div>
                  </div>
                ) : null}
                {secondInterview ? (
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
                      style={{ backgroundColor: tk.primaryFixed, color: tk.onPrimaryFixedVariant }}
                    >
                      <Coffee size={18} aria-hidden />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-bold" style={{ color: tk.onSurface }}>
                        {secondInterview.job.company}
                      </p>
                      <p className="text-xs" style={{ color: tk.onVariant }}>
                        {secondInterview.job.title} · interview stage
                      </p>
                    </div>
                  </div>
                ) : null}
                <Link
                  href="/prep"
                  className="inline-flex items-center gap-1 text-[13px] font-semibold hover:underline"
                  style={{ color: tk.primary }}
                >
                  Interview prep <ChevronRight size={14} />
                </Link>
              </div>
            )}
          </div>

          <div
            className="relative overflow-hidden rounded-xl border-[0.5px] p-6 text-white shadow-sm"
            style={{ backgroundColor: tk.insightBlue, borderColor: tk.insightBlue }}
          >
            <div className="relative z-10">
              <h3 className="text-base font-medium tracking-tight">Market insights</h3>
              <p className="mt-2 text-[13px] leading-relaxed opacity-95">
                High-fit roles in your queue:{' '}
                <span className="font-bold tabular-nums">{summaryLoading ? '…' : highFit}</span>. Remote and hybrid
                listings refresh often — stay current in Discover.
              </p>
              <Link
                href="/discover?q=remote"
                className="mt-6 inline-block rounded border-[0.5px] border-white bg-white px-4 py-2 text-[12px] font-semibold shadow-sm transition hover:bg-zinc-50 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                style={{ color: tk.insightBlue }}
              >
                View salary bands
              </Link>
            </div>
            <BarChart3
              className="pointer-events-none absolute -bottom-4 -right-4 z-0 h-32 w-32 opacity-[0.12]"
              aria-hidden
              strokeWidth={1}
            />
          </div>

          <div className="border-[0.5px] bg-white p-5 dark:bg-slate-900" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-[12px] font-medium uppercase tracking-widest" style={{ color: tk.onVariant }}>
                Resume score
              </h3>
              <span className="text-lg font-black" style={{ color: tk.primary }}>
                {resumeScoreDisplay != null ? `${resumeScoreDisplay}/100` : '—'}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full" style={{ backgroundColor: tk.surfaceHigh }}>
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: resumeScoreDisplay != null ? `${resumeScoreDisplay}%` : '0%',
                  backgroundColor: tk.primary,
                }}
              />
            </div>
            <p className="mt-3 text-xs leading-relaxed" style={{ color: tk.onVariant }}>
              {avgFit != null && avgFit >= 4
                ? 'Strong average fit across scored roles — keep iterating on stories and metrics.'
                : avgFit != null
                  ? 'Improve your score by sharpening skills on your résumé and preferences to match target roles.'
                  : 'Derived from average role fit when scores exist. Upload your résumé to unlock scoring.'}
            </p>
            <Link href="/resume" className="mt-2 inline-block text-[12px] font-medium hover:underline" style={{ color: tk.primary }}>
              My resume
            </Link>
          </div>
        </div>
      </section>

      {/* Recently viewed companies */}
      <section className="space-y-4 pt-2">
        <h3 className="px-1 text-[12px] font-medium uppercase tracking-widest" style={{ color: tk.onVariant }}>
          Recently viewed companies
        </h3>
        {recentCompanies.length === 0 ? (
          <p className="text-[13px]" style={{ color: tk.onVariant }}>
            Companies appear here as you add applications from{' '}
            <Link href="/discover" className="font-semibold hover:underline" style={{ color: tk.primary }}>
              Discover
            </Link>
            .
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-6">
            {recentCompanies.map((name, i) => {
              const CoIcon = companyGridIcons[i % companyGridIcons.length]
              return (
                <Link
                  key={name}
                  href="/pipeline"
                  className="group flex flex-col items-center gap-3 border-[0.5px] bg-white p-4 text-center transition-colors hover:bg-[#f0f5f2] dark:bg-slate-900 dark:hover:bg-slate-800"
                  style={{ borderColor: 'rgba(109,122,119,0.45)' }}
                >
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded border-[0.5px] bg-slate-100"
                    style={{ borderColor: 'rgba(109,122,119,0.45)' }}
                  >
                    <CoIcon size={18} className="text-slate-400" aria-hidden />
                  </div>
                  <span className="text-center text-[12px] font-semibold" style={{ color: tk.onSurface }}>
                    {name}
                  </span>
                </Link>
              )
            })}
          </div>
        )}
      </section>

      {/* Pipeline strip */}
      <section
        className="rounded-xl border-[0.5px] px-4 py-3"
        style={{ borderColor: tk.primary, backgroundColor: tk.primaryFixed }}
      >
        <p className="text-[13px]" style={{ color: tk.onPrimaryFixedVariant }}>
          <span className="font-semibold">Pipeline</span>:{' '}
          <span className="tabular-nums">{summaryLoading ? '…' : pipelineCount}</span> active ·{' '}
          <Link href="/pipeline" className="font-semibold underline-offset-2 hover:underline">
            View pipeline
          </Link>
        </p>
      </section>

      {/* Recent applications & saved */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <article className="border-[0.5px] bg-white p-6 dark:bg-slate-900" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
          <h3 className="text-lg font-medium tracking-tight" style={{ color: tk.onSurface }}>
            Recent applications
          </h3>
          <p className="mt-1 text-sm" style={{ color: tk.onVariant }}>
            Latest updates in your workspace
          </p>
          {appsError ? (
            <p className="mt-4 text-sm text-rose-600">Could not load applications.</p>
          ) : appsLoading ? (
            <p className="mt-4 text-sm text-zinc-500">Loading…</p>
          ) : recentApplications.length === 0 ? (
            <p className="mt-4 text-sm" style={{ color: tk.onVariant }}>
              Nothing yet.{' '}
              <Link href="/discover" className="font-semibold hover:underline" style={{ color: tk.primary }}>
                Discover roles
              </Link>
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {recentApplications.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-3 border-b border-zinc-100 pb-3 last:border-0 last:pb-0"
                >
                  <div className="min-w-0">
                    <p className="text-[14px] font-semibold" style={{ color: tk.onSurface }}>
                      {item.job.title}
                    </p>
                    <p className="text-[12px]" style={{ color: tk.onVariant }}>
                      {item.job.company}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-slate-100 px-2 py-1 text-[11px]" style={{ color: tk.onVariant }}>
                    {formatApplicationStatus(item.status)}
                  </span>
                </div>
              ))}
            </div>
          )}
          <Link
            href="/pipeline"
            className="mt-4 inline-flex items-center gap-1 text-[13px] font-semibold hover:underline"
            style={{ color: tk.primary }}
          >
            All applications <ChevronRight size={14} />
          </Link>
        </article>

        <article className="border-[0.5px] bg-white p-6 dark:bg-slate-900" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
          <h3 className="text-lg font-medium tracking-tight" style={{ color: tk.onSurface }}>
            Saved jobs
          </h3>
          <p className="mt-1 text-sm" style={{ color: tk.onVariant }}>
            Roles marked saved
          </p>
          {appsError ? (
            <p className="mt-4 text-sm text-rose-600">Could not load saved jobs.</p>
          ) : appsLoading ? (
            <p className="mt-4 text-sm text-zinc-500">Loading…</p>
          ) : !allApplications?.some((a) => a.status === 'saved') ? (
            <p className="mt-4 text-sm" style={{ color: tk.onVariant }}>
              No saved roles. Save from{' '}
              <Link href="/discover" className="font-semibold hover:underline" style={{ color: tk.primary }}>
                Discover
              </Link>
              .
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {allApplications
                .filter((a) => a.status === 'saved')
                .slice(0, 5)
                .map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between gap-3 border-b border-zinc-100 pb-3 last:border-0"
                  >
                    <p className="min-w-0 text-[14px] font-semibold" style={{ color: tk.onSurface }}>
                      {item.job.title}
                    </p>
                    <span className="shrink-0 text-[12px]" style={{ color: tk.onVariant }}>
                      {item.job.company}
                    </span>
                  </div>
                ))}
            </div>
          )}
          <Link
            href="/discover"
            className="mt-4 inline-flex items-center gap-1 text-[13px] font-semibold hover:underline"
            style={{ color: tk.primary }}
          >
            Discover more <ChevronRight size={14} />
          </Link>
        </article>
      </section>
    </div>
  )
}
