'use client'

import Link from 'next/link'
import type { Route } from 'next'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useMemo, useState } from 'react'
import { DashboardPageHeader } from '../../components/dashboard/DashboardPageHeader'
import { MatchPipelineUpdateCard } from '../../components/dashboard/MatchPipelineUpdateCard'
import useSWR from 'swr'
import {
  RefreshCw,
  SlidersHorizontal,
  Globe,
  Building2,
  MapPin,
  ArrowRight,
  X,
  BookOpen,
  Search,
  Filter,
  Sparkles,
} from 'lucide-react'
import { cn, fitClass, channelLabel, channelBadgeClass, relativeTime, scoreBarWidth } from '../../lib/utils'
import { useJobs } from './useJobs'
import { usePipeline } from '../pipeline/usePipeline'
import { useJobStore } from './jobStore'
import { applicationsApi, resumeApi, telemetryApi } from '../../lib/api'
import { resolveJobListingUrl } from './jobListingUrl'
import { candidatePageShell, candidateTokens } from '../../lib/candidateUi'
import {
  AnimatePresence,
  fadeInUpVariants,
  getMicroInteractionMotion,
  motion,
  staggerContainerVariants,
  useReducedMotion,
} from '../../lib/motion'
import { useDashboard } from '../../hooks/useDashboard'
import type { JobWithScore } from '@doubow/shared'
import { AnimatedMetricValue } from './discoverShared'
import { useDiscoverController } from './useDiscoverController'
import { DiscoverFiltersSection } from './DiscoverFiltersSection'
import { DiscoverResultsSection } from './DiscoverResultsSection'
import { DiscoverJobsList } from './DiscoverJobsList'
import { useDiscoverTelemetry } from './useDiscoverTelemetry'

const MotionLink = motion(Link)

const DIMENSION_LABELS: Record<string, string> = {
  tech: 'Tech match', culture: 'Culture', seniority: 'Seniority', comp: 'Compensation', location: 'Location',
}
const SOURCE_LABELS: Record<JobWithScore['source'], string> = {
  adzuna: 'Adzuna',
  ashby: 'Ashby',
  google_jobs: 'Google Jobs',
  greenhouse: 'Greenhouse',
  lever: 'Lever',
  linkedin: 'LinkedIn',
  wellfound: 'Wellfound',
  manual: 'Manual',
  catalog: 'Company site',
}

function scoreProvenanceLabel(provenance: JobWithScore['score']['provenance']): string {
  if (provenance === 'computed') return 'Based on your profile'
  if (provenance === 'template_default') return 'Starting estimate'
  if (provenance === 'template_seeded') return 'From your setup'
  return 'Still updating'
}

function scoreProvenanceClass(provenance: JobWithScore['score']['provenance']): string {
  if (provenance === 'computed') return 'bg-emerald-100 text-emerald-800'
  if (provenance === 'template_default') return 'bg-amber-100 text-amber-900'
  if (provenance === 'template_seeded') return 'bg-zinc-100 text-zinc-700'
  return 'bg-rose-100 text-rose-800'
}

function sourceLabel(source: JobWithScore['source']): string {
  return SOURCE_LABELS[source] ?? 'Source'
}

function descriptionPreview(text?: string, max = 180): string {
  const normalized = (text ?? '').replace(/\s+/g, ' ').trim()
  if (!normalized) return 'No source description available for this listing.'
  if (normalized.length <= max) return normalized
  return `${normalized.slice(0, max).trimEnd()}…`
}

function FitBadge({ score }: { score: number }) {
  return (
    <span className={cn('badge text-xs px-2 py-0.5', fitClass(score))}>
      {score.toFixed(1)}
    </span>
  )
}

function CompanyLogo({
  company,
  logoUrl,
  imageSize,
  className,
}: {
  company: string
  logoUrl?: string | null
  imageSize: number
  className?: string
}) {
  const [failed, setFailed] = useState(false)
  const initials = company.slice(0, 2).toUpperCase()
  const safeLogoUrl = useMemo(() => {
    if (!logoUrl) return logoUrl
    const normalized = logoUrl.replace('job-boards.greenhouse.io', 'boards.greenhouse.io')
    // If Greenhouse hosts are failing DNS in the browser, skip external logo fetches.
    if (normalized.includes('boards.greenhouse.io') || normalized.includes('job-boards.greenhouse.io')) {
      return null
    }
    return normalized
  }, [logoUrl])

  useEffect(() => {
    setFailed(false)
  }, [safeLogoUrl, company])

  if (!safeLogoUrl || failed) {
    return <span className={cn('text-xs font-semibold text-zinc-700', className)}>{initials}</span>
  }

  return (
    <img
      src={safeLogoUrl}
      alt={`${company} logo`}
      className={cn('object-contain opacity-90', className)}
      width={imageSize}
      height={imageSize}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}

function JobCard({ job, motionEnabled }: { job: JobWithScore; motionEnabled: boolean }) {
  const [queuing, setQueuing] = useState(false)
  const [queued, setQueued] = useState(false)
  const [queueError, setQueueError] = useState<string | null>(null)
  const [isHydrated, setIsHydrated] = useState(false)
  const dismissJob = useJobStore((s) => s.dismissJob)
  const queueIdempotencyKey = useMemo(() => crypto.randomUUID(), [])

  useEffect(() => {
    setIsHydrated(true)
  }, [])

  async function handleQueue() {
    setQueuing(true)
    setQueueError(null)
    try {
      await applicationsApi.create(job.id, job.score.channel_recommendation, {
        idempotencyKey: queueIdempotencyKey,
      })
      setQueued(true)
    } catch {
      setQueueError('Could not add to queue. Retry in a moment.')
    } finally {
      setQueuing(false)
    }
  }

  const dims = Object.entries(job.score.dimension_scores) as [string, number][]
  const hasGap = job.score.risk_flags.length > 0
  const ctaMotion = motionEnabled
    ? {
        whileHover: { y: -1, scale: 1.01 },
        whileTap: { scale: 0.99 },
      }
    : {}

  return (
    <motion.div
      layout={motionEnabled}
      variants={motionEnabled ? fadeInUpVariants : undefined}
      initial={motionEnabled ? 'hidden' : false}
      animate={motionEnabled ? 'visible' : undefined}
      exit={motionEnabled ? 'exit' : undefined}
      className={cn('card animate-fade-in transition-all', queued && 'opacity-60 pointer-events-none')}
    >
      <div className="p-4">
        {/* Top row */}
        <div className="mb-2 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center border border-[0.5px] border-zinc-200 bg-zinc-50">
              <CompanyLogo company={job.company} logoUrl={job.logo_url} imageSize={32} className="h-8 w-8" />
            </div>
            <div>
              <p className="text-sm font-medium leading-snug text-zinc-900">{job.title}</p>
              <p className="mt-0.5 text-xs text-zinc-500">{job.company}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <FitBadge score={job.score.fit_score} />
            <button
              onClick={() => dismissJob(job.id)}
              className="text-zinc-400 transition-colors hover:text-zinc-600"
            >
              <X size={13} />
            </button>
          </div>
        </div>

        {/* Meta */}
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1 text-xs text-zinc-600">
            <Building2 size={12} />
            {job.company}
          </span>
          <span className="inline-flex items-center gap-1 text-xs text-zinc-600">
            {job.location?.toLowerCase().includes('remote') ? <Globe size={12} /> : <MapPin size={12} />}
            {job.location}
          </span>
          {job.salary_range && (
            <span className="text-xs font-medium text-primary-green">{job.salary_range}</span>
          )}
          <span className={cn('badge text-2xs', channelBadgeClass(job.score.channel_recommendation))}>
            via {channelLabel(job.score.channel_recommendation)}
          </span>
          <span className="text-xs font-medium text-zinc-500">Source: {sourceLabel(job.source)}</span>
          <span className="text-xs text-zinc-500">{isHydrated ? relativeTime(job.discovered_at) : '—'}</span>
        </div>

        <div className="rounded-sm border border-[0.5px] bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-zinc-500">
            Description from {sourceLabel(job.source)}
          </p>
          <p>{descriptionPreview(job.description, 210)}</p>
        </div>

        <div className="mt-3 grid grid-cols-5 gap-4 border-t border-[0.5px] pt-3" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
          {dims.map(([k, v]) => (
            <div key={k} className="space-y-1">
              <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-zinc-500">{DIMENSION_LABELS[k] ?? k}</p>
              <div className="h-1 w-full bg-zinc-100">
                <div
                  className={cn('h-full', hasGap && k === 'tech' ? 'bg-amber-500' : 'bg-primary-green')}
                  style={{ width: `${scoreBarWidth(v)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="mt-2">
          <span
            className={cn(
              'inline-flex rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em]',
              scoreProvenanceClass(job.score.provenance),
            )}
          >
            How we scored this: {scoreProvenanceLabel(job.score.provenance)}
          </span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <MotionLink
            href={`/discover/${job.id}` as Route}
            {...ctaMotion}
            className={cn(
              'inline-flex h-9 flex-1 items-center justify-center gap-1 border border-[0.5px] px-3 text-[11px] font-semibold uppercase tracking-[0.1em] transition-colors',
              hasGap
                ? 'border-zinc-200 bg-white dark:bg-slate-900 text-zinc-600 hover:bg-zinc-50'
                : 'border-primary-green bg-white dark:bg-slate-900 text-primary-green hover:bg-bg-light-green',
            )}
          >
            <BookOpen size={12} />
            {hasGap ? 'Review Gaps' : 'Details & Analysis'}
          </MotionLink>
          {queued ? (
            <span className="text-xs font-medium text-emerald-700">✓ Added to queue</span>
          ) : (
            <motion.button
              onClick={handleQueue}
              disabled={queuing}
              {...ctaMotion}
              className={cn(
                'inline-flex h-9 flex-1 items-center justify-center gap-1 border border-[0.5px] px-3 text-[11px] font-semibold uppercase tracking-[0.1em] transition-colors',
                hasGap
                  ? 'border-primary-green bg-white dark:bg-slate-900 text-primary-green hover:bg-bg-light-green'
                  : 'border-primary-green bg-primary-green text-white hover:bg-primary-green-hover',
              )}
            >
              {queuing ? 'Preparing…' : hasGap ? 'Bypass & Apply' : 'Initiate Application'}
              {!queuing && <ArrowRight size={12} />}
            </motion.button>
          )}
          {queueError ? <span className="text-xs font-medium text-rose-700">{queueError}</span> : null}
        </div>
      </div>
    </motion.div>
  )
}

function CatalogFeaturedMatch({ job, motionEnabled }: { job: JobWithScore; motionEnabled: boolean }) {
  const [queuing, setQueuing] = useState(false)
  const [queued, setQueued] = useState(false)
  const [queueError, setQueueError] = useState<string | null>(null)
  const queueKey = useMemo(() => crypto.randomUUID(), [])
  const fitPct = Math.min(100, Math.round((job.score.fit_score / 5) * 100))

  async function handleQueue() {
    setQueuing(true)
    setQueueError(null)
    try {
      await applicationsApi.create(job.id, job.score.channel_recommendation, {
        idempotencyKey: queueKey,
      })
      setQueued(true)
    } catch {
      setQueueError('Queue failed. Please retry.')
    } finally {
      setQueuing(false)
    }
  }

  const dims = Object.entries(job.score.dimension_scores) as [string, number][]
  const ctaMotion = motionEnabled
    ? {
        whileHover: { y: -1, scale: 1.01 },
        whileTap: { scale: 0.99 },
      }
    : {}

  return (
    <article
      className="border-[0.5px] border-l-4 bg-white dark:bg-slate-900 p-4 shadow-sm lg:col-span-12"
      style={{ borderColor: candidateTokens.outline, borderLeftColor: candidateTokens.amber }}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 flex-1 gap-4">
          <div
            className="flex h-16 w-16 flex-shrink-0 items-center justify-center border-[0.5px] bg-[#f0f5f2] text-sm font-bold text-primary-green"
            style={{ borderColor: candidateTokens.outline }}
          >
            <CompanyLogo company={job.company} logoUrl={job.logo_url} imageSize={44} className="h-11 w-11 text-sm font-bold text-primary-green" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold leading-snug text-zinc-900">{job.title}</h3>
              <span className="rounded bg-highlight-green px-2 py-0.5 text-[10px] font-bold uppercase tracking-tight text-primary-green">
                {fitPct}% match
              </span>
            </div>
            <p className="mt-1 text-sm text-zinc-600">
              {job.company} · {job.location ?? 'Location TBD'}
            </p>
          </div>
        </div>
        <div className="text-right lg:pl-4">
          <div className="text-[32px] font-black leading-none tracking-tighter text-primary-green">
            {job.score.fit_score.toFixed(2)}
          </div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">Fit index</p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
        {dims.map(([k, v]) => (
          <div
            key={k}
            className="border-[0.5px] bg-[#f0f5f2] p-3"
            style={{ borderColor: candidateTokens.outline }}
          >
            <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-zinc-500">
              {DIMENSION_LABELS[k] ?? k}
            </p>
            <div className="flex items-center gap-2">
              <div className="h-1 flex-1 overflow-hidden rounded-full bg-zinc-200">
                <div
                  className="h-full rounded-full bg-primary-green"
                  style={{ width: `${scoreBarWidth(v)}%` }}
                />
              </div>
              <span className="text-[11px] font-semibold tabular-nums text-zinc-700">
                {Math.round(scoreBarWidth(v))}%
              </span>
            </div>
          </div>
        ))}
      </div>

      <div
        className="mt-4 rounded-sm border border-[0.5px] bg-[#f7faf8] p-3"
        style={{ borderColor: candidateTokens.outline }}
      >
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-zinc-500">
          Description from {sourceLabel(job.source)}
        </p>
        <p className="text-xs leading-relaxed text-zinc-700">{descriptionPreview(job.description, 260)}</p>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-zinc-100 pt-4">
        {queued ? (
          <span className="text-sm font-medium text-emerald-700">Added to your pipeline</span>
        ) : (
          <motion.button
            type="button"
            onClick={() => void handleQueue()}
            disabled={queuing}
            {...ctaMotion}
            className="btn btn-primary text-xs inline-flex items-center gap-1.5"
          >
            {queuing ? 'Queueing…' : 'Prepare application'}
            {!queuing ? <ArrowRight size={12} /> : null}
          </motion.button>
        )}
        {queueError ? <span className="text-sm font-medium text-rose-700">{queueError}</span> : null}
        <MotionLink href="/prep" {...ctaMotion} className="btn text-xs inline-flex items-center gap-1.5">
          <BookOpen size={12} />
          Interview prep
        </MotionLink>
        <MotionLink href={`/discover/${job.id}` as Route} {...ctaMotion} className="btn text-xs inline-flex items-center gap-1.5">
          View details
        </MotionLink>
        <motion.a
          href={resolveJobListingUrl(job)}
          target="_blank"
          rel="noopener noreferrer"
          {...ctaMotion}
          className="btn btn-ghost text-xs ml-auto"
        >
          View listing ↗
        </motion.a>
      </div>
    </article>
  )
}

function JobSkeleton() {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex gap-3">
        <div className="skeleton w-9 h-9 rounded-md flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-3.5 w-48 rounded" />
          <div className="skeleton h-3 w-28 rounded" />
        </div>
        <div className="skeleton h-5 w-10 rounded-full" />
      </div>
      <div className="flex gap-3">
        <div className="skeleton h-3 w-24 rounded" />
        <div className="skeleton h-3 w-20 rounded" />
      </div>
    </div>
  )
}

function DiscoverPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const {
    jobs,
    loading,
    minFit,
    setMinFit,
    locationFilter,
    setLocationFilter,
    hasSalaryOnly,
    setHasSalaryOnly,
  } = useJobStore()
  usePipeline()
  const { summary, loading: dashLoading, refresh: refreshDashboard } = useDashboard()
  const { refresh: refreshJobs } = useJobs()
  const { data: onboarding, mutate: refreshOnboarding } = useSWR(
    'onboarding-status',
    resumeApi.onboardingStatus,
    {
      revalidateOnFocus: false,
      refreshInterval: (current) => (current?.state === 'scoring_in_progress' ? 5000 : 0),
    },
  )
  const { data: activationKpi, isLoading: activationKpiLoading, mutate: refreshActivationKpi } = useSWR(
    'activation-kpi',
    telemetryApi.activationKpi,
    { revalidateOnFocus: true, dedupingInterval: 30_000 },
  )
  const [filterOpen, setFilterOpen] = useState(false)
  const {
    searchText,
    setSearchText,
    sortBy,
    setSortBy,
    filteredJobs,
    sortedJobs,
    minFitChip,
    precisionMode,
    clearSearch,
    resetSearchAndFilters,
  } = useDiscoverController({
    jobs,
    minFit,
    locationFilter,
    hasSalaryOnly,
    setMinFit,
    setLocationFilter,
    setHasSalaryOnly,
    searchParams,
    router,
  })
  const prefersReducedMotion = useReducedMotion()
  const motionEnabled = !prefersReducedMotion
  const microInteractionMotion = getMicroInteractionMotion(motionEnabled)
  const iconTapMotion = motionEnabled
    ? {
        whileTap: { scale: 0.9 },
        transition: { duration: 0.14, ease: 'easeOut' as const },
      }
    : {}
  const topMatch = sortedJobs[0]
  const showFeaturedCard =
    !loading && Boolean(topMatch) && sortedJobs.length > 0 && onboarding?.state !== 'scoring_in_progress'
  const jobsForList = showFeaturedCard ? sortedJobs.slice(1) : sortedJobs

  const highFitVisible = filteredJobs.filter((j) => j.score.fit_score >= 4).length
  const etaMinutes = onboarding?.eta_seconds ? Math.max(1, Math.round(onboarding.eta_seconds / 60)) : null
  const avgTimeMinutes = activationKpi?.avg_time_to_first_matches_seconds != null
    ? Math.max(1, Math.round(activationKpi.avg_time_to_first_matches_seconds / 60))
    : null
  const latestTimeMinutes = activationKpi?.latest_time_to_first_matches_seconds != null
    ? Math.max(1, Math.round(activationKpi.latest_time_to_first_matches_seconds / 60))
    : null

  useDiscoverTelemetry({
    onboarding,
    jobsLength: jobs.length,
    refreshJobs,
  })

  const statCards = useMemo(() => {
    if (!summary) {
      return [
        { label: 'Evaluated this week', value: dashLoading ? '…' : '-', sub: 'scores since Mon UTC' },
        { label: 'High fit (>= 4.0)', value: dashLoading ? '…' : '-', sub: 'ready to review' },
        { label: 'Avg fit score', value: dashLoading ? '…' : '-', sub: 'all scored roles' },
        { label: 'Applied', value: dashLoading ? '…' : '-', sub: 'awaiting reply or next step' },
        { label: 'Time to first matches', value: activationKpiLoading ? '…' : '-', sub: 'activation KPI' },
      ]
    }
    return [
      {
        label: 'Evaluated this week',
        value: String(summary.evaluated_this_week),
        sub: 'scores since Mon UTC',
      },
      {
        label: 'High fit (>= 4.0)',
        value: String(summary.high_fit_count),
        sub: 'ready to review',
      },
      {
        label: 'Avg fit score',
        value: summary.avg_fit_score != null ? summary.avg_fit_score.toFixed(1) : '-',
        sub: 'all scored roles',
      },
      {
        label: 'Applied',
        value: String(summary.applied_awaiting_reply),
        sub: 'awaiting reply or next step',
      },
      {
        label: 'Time to first matches',
        value: avgTimeMinutes != null
          ? `~${avgTimeMinutes}m avg${latestTimeMinutes != null ? ` · ${latestTimeMinutes}m latest` : ''}`
          : latestTimeMinutes != null
          ? `${latestTimeMinutes}m latest`
          : '-',
        sub: activationKpi?.sample_size ? `from ${activationKpi.sample_size} run${activationKpi.sample_size > 1 ? 's' : ''}` : 'activation KPI',
      },
    ]
  }, [summary, dashLoading, activationKpi, activationKpiLoading, avgTimeMinutes, latestTimeMinutes])

  async function handleRefresh() {
    await refreshJobs()
    await refreshOnboarding()
    await refreshDashboard()
    await refreshActivationKpi()
  }

  return (
    <div className={candidatePageShell}>
      <DashboardPageHeader
        kicker={precisionMode ? 'Focused search' : 'Job discovery'}
        title={precisionMode ? 'Refined job matches' : 'Job catalog'}
        description={
          precisionMode
            ? 'Narrowed results based on your filters and fit scoring.'
            : 'AI-scored roles from your resume — filter, queue, and prep in one workspace.'
        }
        actions={
          <>
            <Link
              href="/messages"
              className="inline-flex items-center gap-1.5 rounded-sm border border-primary-green bg-primary-green px-3 py-2 text-[14px] font-medium text-white shadow-sm transition-opacity hover:opacity-95"
            >
              <Sparkles size={13} aria-hidden />
              Assistant
            </Link>
            <motion.button
              type="button"
              onClick={() => setFilterOpen((x) => !x)}
              {...microInteractionMotion}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-sm border px-3 py-2 text-[14px] font-medium shadow-sm transition-colors',
                filterOpen
                  ? 'border-secondary-green/30 bg-bg-light-green text-primary-green'
                  : 'border-[#e4e5ec] bg-white dark:bg-slate-900 text-zinc-700 hover:bg-zinc-50',
              )}
            >
              <motion.span {...iconTapMotion} className="inline-flex">
                <SlidersHorizontal size={13} />
              </motion.span>
              Filters
            </motion.button>
            <motion.button
              type="button"
              onClick={() => void handleRefresh()}
              {...microInteractionMotion}
              className="inline-flex items-center gap-1.5 rounded-sm border border-[#e4e5ec] bg-white dark:bg-slate-900 px-3 py-2 text-[14px] font-medium text-zinc-700 shadow-sm hover:bg-zinc-50"
            >
              <motion.span {...iconTapMotion} className="inline-flex">
                <RefreshCw size={13} className={cn((loading || dashLoading) && 'animate-spin-slow')} />
              </motion.span>
              Refresh
            </motion.button>
          </>
        }
      />

      <MatchPipelineUpdateCard
        onAfterRun={async () => {
          await handleRefresh()
        }}
      />

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-xl">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" aria-hidden />
          <input
            type="search"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search title, company, keywords…"
            className="field w-full pl-10"
            aria-label="Search jobs"
          />
        </div>
        <div className="flex items-center gap-2 sm:shrink-0">
          <label className="text-2xs font-semibold uppercase tracking-wider text-zinc-400">
            Sort
            <select
              className="field ml-2 w-36 py-1 text-xs"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'fit' | 'recent' | 'company')}
            >
              <option value="fit">Best fit</option>
              <option value="recent">Most recent</option>
              <option value="company">Company A-Z</option>
            </select>
          </label>
          {searchText.trim() ? (
            <motion.button
              type="button"
              className="text-xs font-medium text-zinc-500 hover:text-zinc-800"
              {...microInteractionMotion}
              onClick={clearSearch}
            >
              Clear search
            </motion.button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2 text-sm text-zinc-600">
          <span className="text-2xs font-semibold uppercase tracking-wider text-zinc-400">Global discovery</span>
          <span className="text-zinc-300" aria-hidden>
            ·
          </span>
          <span className="text-[13px] text-zinc-700">
            {locationFilter.trim() ? locationFilter.trim() : 'All locations'}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span
            className="inline-flex items-center rounded-full border border-[#e4e5ec] bg-zinc-50 px-2 py-1 text-2xs font-semibold text-zinc-700"
          >
            Min score: {minFitChip}
          </span>
          <motion.button
            type="button"
            onClick={() => setFilterOpen((x) => !x)}
            {...microInteractionMotion}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-sm border px-2 py-1 text-2xs font-semibold transition-colors',
              filterOpen ? 'border-secondary-green/45 bg-bg-light-green text-primary-green' : 'border-[#e4e5ec] bg-white dark:bg-slate-900 text-zinc-700 hover:bg-zinc-50',
            )}
          >
            <motion.span {...iconTapMotion} className="inline-flex">
              <Filter size={12} aria-hidden />
            </motion.span>
            Refine parameters
          </motion.button>
          {locationFilter.trim() ? (
            <motion.button
              type="button"
              onClick={() => setLocationFilter('')}
              {...microInteractionMotion}
              className="inline-flex items-center gap-1 rounded-full border border-secondary-green/30 bg-bg-light-green px-2 py-1 text-2xs font-semibold text-primary-green"
            >
              Location: {locationFilter.trim()}
              <motion.span {...iconTapMotion} className="inline-flex">
                <X size={11} />
              </motion.span>
            </motion.button>
          ) : null}
          {sortBy !== 'fit' ? (
            <motion.button
              type="button"
              onClick={() => setSortBy('fit')}
              {...microInteractionMotion}
              className="inline-flex items-center gap-1 rounded-full border border-zinc-200 bg-zinc-50 px-2 py-1 text-2xs font-semibold text-zinc-700"
            >
              Sort: {sortBy === 'recent' ? 'Most recent' : 'Company A-Z'}
              <motion.span {...iconTapMotion} className="inline-flex">
                <X size={11} />
              </motion.span>
            </motion.button>
          ) : null}
        </div>
      </div>

      <DiscoverFiltersSection
        locationFilter={locationFilter}
        setLocationFilter={setLocationFilter}
        minFit={minFit}
        setMinFit={setMinFit}
        setSearchText={setSearchText}
        setSortBy={setSortBy}
        microInteractionMotion={microInteractionMotion}
      />

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <aside className="space-y-3 lg:col-span-4">
          <article
            className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-3"
            style={{ borderColor: 'rgba(109,122,119,0.45)' }}
          >
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
              {precisionMode ? 'Refined filters' : 'Advanced filters'}
            </p>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  Precise location
                </label>
                <input
                  className="field py-1 text-xs"
                  placeholder="San Francisco, CA (Remote Friendly)"
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                />
              </div>
              <div>
                <div className="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  <span>Minimum fit score</span>
                  <span className="text-primary-green">{minFitChip}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={4.5}
                  step={0.5}
                  value={minFit}
                  onChange={(e) => setMinFit(Number(e.target.value))}
                  className="w-full accent-primary-green"
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  Active criteria
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    locationFilter.trim() ? `Location: ${locationFilter.trim()}` : null,
                    minFit > 0 ? `Min fit: ${minFitChip}` : null,
                    searchText.trim() ? `Query: ${searchText.trim()}` : null,
                    hasSalaryOnly ? 'Salary only' : null,
                  ]
                    .filter((item): item is string => Boolean(item))
                    .map((item) => (
                      <span
                        key={item}
                        className="rounded-sm border border-secondary-green/30 bg-bg-light-green px-2 py-1 text-[10px] font-semibold text-primary-green"
                      >
                        {item}
                      </span>
                    ))}
                  {!locationFilter.trim() && minFit === 0 && !searchText.trim() && !hasSalaryOnly ? (
                    <p className="text-[11px] text-zinc-500">
                      No criteria applied yet. Use filters to refine your matches.
                    </p>
                  ) : null}
                </div>
              </div>
            </div>
          </article>

          <article
            className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-3"
            style={{ borderColor: 'rgba(109,122,119,0.45)' }}
          >
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
              {precisionMode ? 'Overall match score' : 'Your match score'}
            </p>
            <p className="text-2xl font-bold text-primary-green">
              <AnimatedMetricValue
                value={summary?.avg_fit_score != null ? `${(summary.avg_fit_score * 20).toFixed(1)}` : '—'}
              />
            </p>
            <p className="text-[10px] text-zinc-500">
              {precisionMode
                ? 'Combined fit score for your current filtered view'
                : 'Based on role, skills, compensation, location, and seniority'}
            </p>
          </article>
        </aside>

        <DiscoverResultsSection
          filteredCount={filteredJobs.length}
          precisionMode={precisionMode}
          sortBy={sortBy}
        />
      </section>

      <AnimatePresence initial={false} mode="wait">
        {showFeaturedCard && topMatch ? (
          <motion.div
            key={`featured-${topMatch.id}`}
            layout={motionEnabled}
            variants={motionEnabled ? fadeInUpVariants : undefined}
            initial={motionEnabled ? 'hidden' : false}
            animate={motionEnabled ? 'visible' : undefined}
            exit={motionEnabled ? 'exit' : undefined}
          >
            <CatalogFeaturedMatch job={topMatch} motionEnabled={motionEnabled} />
          </motion.div>
        ) : null}
      </AnimatePresence>

      <DiscoverJobsList
        loading={loading}
        jobsLength={jobs.length}
        filteredJobs={filteredJobs}
        jobsForList={jobsForList}
        onboarding={onboarding}
        etaMinutes={etaMinutes}
        motionEnabled={motionEnabled}
        onResetFilters={resetSearchAndFilters}
        renderJobCard={(job) => <JobCard key={job.id} job={job} motionEnabled={motionEnabled} />}
        renderJobSkeleton={(idx) => <JobSkeleton key={idx} />}
      />
    </div>
  )
}

function DiscoverPageFallback() {
  return (
    <div className={candidatePageShell}>
      <div className="h-10 w-64 max-w-full animate-pulse rounded-lg bg-zinc-100" />
      <div className="h-11 max-w-xl animate-pulse rounded-lg bg-zinc-100" />
      <div className="grid gap-3 lg:grid-cols-12">
        <div className="h-48 animate-pulse rounded-sm bg-zinc-100 lg:col-span-6" />
        <div className="h-24 animate-pulse rounded-sm bg-zinc-100 lg:col-span-6" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <JobSkeleton key={i} />
        ))}
      </div>
    </div>
  )
}

export default function DiscoverPage() {
  return (
    <Suspense fallback={<DiscoverPageFallback />}>
      <DiscoverPageContent />
    </Suspense>
  )
}
