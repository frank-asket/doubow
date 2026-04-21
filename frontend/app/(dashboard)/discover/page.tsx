'use client'

import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'
import useSWR from 'swr'
import { RefreshCw, SlidersHorizontal, Globe, ChevronDown, ChevronUp, ArrowRight, X, BookOpen, ShieldCheck, Timer } from 'lucide-react'
import { cn, fitClass, fitLabel, channelLabel, channelBadgeClass, relativeTime, scoreBarWidth } from '@/lib/utils'
import { useJobs } from '@/hooks/useJobs'
import { usePipeline } from '@/hooks/usePipeline'
import { useJobStore } from '@/stores/jobStore'
import { usePipelineStore } from '@/stores/pipelineStore'
import { applicationsApi, resumeApi, telemetryApi } from '@/lib/api'
import { clearActivationStart, getActivationStartAt, trackEvent } from '@/lib/telemetry'
import { useDashboard } from '@/hooks/useDashboard'
import type { JobWithScore } from '@/types'

const DIMENSION_LABELS: Record<string, string> = {
  tech: 'Tech match', culture: 'Culture', seniority: 'Seniority', comp: 'Compensation', location: 'Location',
}
const ONBOARDING_STEP_LABELS: Record<string, string> = {
  upload_complete: 'Upload complete',
  parsing_resume: 'Parsing resume',
  scoring_job_matches: 'Scoring job matches',
  building_first_queue: 'Building your first queue',
  first_jobs_ready: 'First jobs ready',
}

function FitBadge({ score }: { score: number }) {
  return (
    <span className={cn('badge text-xs px-2 py-0.5', fitClass(score))}>
      {score.toFixed(1)}
    </span>
  )
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 flex-shrink-0 text-xs text-zinc-500">{DIMENSION_LABELS[label] ?? label}</span>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-zinc-900">
        <div
          className="h-full rounded-full bg-emerald-400 transition-all duration-500"
          style={{ width: `${scoreBarWidth(value)}%` }}
        />
      </div>
      <span className="w-6 text-right text-xs tabular-nums text-zinc-400">{value.toFixed(1)}</span>
    </div>
  )
}

function JobCard({ job }: { job: JobWithScore }) {
  const [expanded, setExpanded] = useState(false)
  const [queuing, setQueuing] = useState(false)
  const [queued, setQueued] = useState(false)
  const dismissJob = useJobStore((s) => s.dismissJob)
  const queueIdempotencyKey = useMemo(() => crypto.randomUUID(), [job.id])

  async function handleQueue() {
    setQueuing(true)
    try {
      await applicationsApi.create(job.id, job.score.channel_recommendation, {
        idempotencyKey: queueIdempotencyKey,
      })
      setQueued(true)
    } catch {
      // optimistic anyway in demo
      setQueued(true)
    } finally {
      setQueuing(false)
    }
  }

  return (
    <div className={cn('card animate-fade-in transition-all', queued && 'opacity-60 pointer-events-none')}>
      <div className="p-4">
        {/* Top row */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900 text-xs font-semibold text-zinc-300">
              {job.company.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium leading-snug text-zinc-100">{job.title}</p>
              <p className="mt-0.5 text-xs text-zinc-400">{job.company}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <FitBadge score={job.score.fit_score} />
            <button
              onClick={() => dismissJob(job.id)}
              className="text-zinc-600 transition-colors hover:text-zinc-300"
            >
              <X size={13} />
            </button>
          </div>
        </div>

        {/* Meta */}
        <div className="flex flex-wrap gap-3 mb-3">
          <span className="text-xs text-zinc-500">📍 {job.location}</span>
          {job.salary_range && (
            <span className="text-xs text-zinc-500">💰 {job.salary_range}</span>
          )}
          <span className={cn('badge text-2xs', channelBadgeClass(job.score.channel_recommendation))}>
            via {channelLabel(job.score.channel_recommendation)}
          </span>
          <span className="text-xs text-zinc-500">{relativeTime(job.discovered_at)}</span>
        </div>

        {/* Expand/collapse */}
        <button
          onClick={() => setExpanded((x) => !x)}
          className="mb-3 flex items-center gap-1 text-xs text-zinc-500 transition-colors hover:text-zinc-300"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Less detail' : 'View fit breakdown'}
        </button>

        {expanded && (
          <div className="space-y-4 pb-1 animate-slide-up">
            {/* Reasons */}
            <div>
              <p className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-zinc-500">Why it matches</p>
              <ul className="space-y-1">
                {job.score.fit_reasons.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-zinc-300">
                    <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-emerald-400" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>

            {/* Risks */}
            {job.score.risk_flags.length > 0 && (
              <div>
                <p className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-zinc-500">Watch out</p>
                <ul className="space-y-1">
                  {job.score.risk_flags.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-rose-300">
                      <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-rose-400" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Score bars */}
            <div>
              <p className="mb-2 text-2xs font-medium uppercase tracking-wider text-zinc-500">Fit dimensions</p>
              <div className="space-y-1.5">
                {Object.entries(job.score.dimension_scores).map(([k, v]) => (
                  <ScoreBar key={k} label={k} value={v} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 border-t border-zinc-800 pt-2">
          {queued ? (
            <span className="text-xs font-medium text-emerald-300">✓ Added to queue</span>
          ) : (
            <button
              onClick={handleQueue}
              disabled={queuing}
              className="btn btn-primary text-xs gap-1.5"
            >
              {queuing ? 'Preparing…' : 'Prepare application'}
              {!queuing && <ArrowRight size={12} />}
            </button>
          )}
          <button className="btn text-xs gap-1.5">
            <BookOpen size={12} />
            Interview prep
          </button>
          <a href={job.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost text-xs ml-auto">
            View JD ↗
          </a>
        </div>
      </div>
    </div>
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

export default function DiscoverPage() {
  const { jobs, loading, minFit, setMinFit } = useJobStore()
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
  const emptyTracked = useRef(false)
  const scoringTracked = useRef(false)
  const etaTracked = useRef(false)
  const readyTracked = useRef(false)

  const filteredJobs = jobs.filter((j) => !minFit || j.score.fit_score >= minFit)
  const etaMinutes = onboarding?.eta_seconds ? Math.max(1, Math.round(onboarding.eta_seconds / 60)) : null
  const onboardingSteps = [
    'upload_complete',
    'parsing_resume',
    'scoring_job_matches',
    'building_first_queue',
  ] as const
  const avgTimeMinutes = activationKpi?.avg_time_to_first_matches_seconds != null
    ? Math.max(1, Math.round(activationKpi.avg_time_to_first_matches_seconds / 60))
    : null
  const latestTimeMinutes = activationKpi?.latest_time_to_first_matches_seconds != null
    ? Math.max(1, Math.round(activationKpi.latest_time_to_first_matches_seconds / 60))
    : null

  useEffect(() => {
    if (onboarding?.state === 'ready' && jobs.length === 0) {
      void refreshJobs()
    }
  }, [onboarding?.state, jobs.length, refreshJobs])

  useEffect(() => {
    if (onboarding?.state === 'no_resume' && !emptyTracked.current) {
      trackEvent('discover_empty_viewed')
      emptyTracked.current = true
      return
    }
    if (onboarding?.state !== 'no_resume') {
      emptyTracked.current = false
    }
  }, [onboarding?.state])

  useEffect(() => {
    if (onboarding?.state === 'scoring_in_progress' && !scoringTracked.current) {
      trackEvent('match_scoring_started', { step: onboarding.current_step })
      scoringTracked.current = true
      return
    }
    if (onboarding?.state !== 'scoring_in_progress') {
      scoringTracked.current = false
    }
  }, [onboarding?.state, onboarding?.current_step])

  useEffect(() => {
    if (onboarding?.state === 'scoring_in_progress' && onboarding.eta_seconds != null && !etaTracked.current) {
      trackEvent('match_scoring_eta_shown', { eta_seconds: onboarding.eta_seconds })
      etaTracked.current = true
      return
    }
    if (onboarding?.state !== 'scoring_in_progress') {
      etaTracked.current = false
    }
  }, [onboarding?.state, onboarding?.eta_seconds])

  useEffect(() => {
    if (onboarding?.state === 'ready' && !readyTracked.current) {
      const startedAt = getActivationStartAt()
      const nowIso = new Date().toISOString()
      let timeToFirstMatchesSeconds: number | null = null
      if (startedAt) {
        const delta = (Date.parse(nowIso) - Date.parse(startedAt)) / 1000
        if (Number.isFinite(delta) && delta >= 0) {
          timeToFirstMatchesSeconds = delta
        }
      }
      trackEvent('first_matches_ready', {
        time_to_first_matches_seconds: timeToFirstMatchesSeconds,
        first_jobs_count: jobs.length,
      })
      clearActivationStart()
      readyTracked.current = true
      return
    }
    if (onboarding?.state !== 'ready') {
      readyTracked.current = false
    }
  }, [onboarding?.state, jobs.length])

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
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-3 rounded-3xl border border-zinc-800 bg-[#080808] p-5 sm:flex-row sm:items-start sm:p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Discover</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Discover</h1>
          <p className="mt-2 text-sm text-zinc-400 sm:text-base">AI-matched roles based on your resume and preferences</p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => setFilterOpen((x) => !x)}
            className={cn('btn text-xs gap-1.5', filterOpen && 'border-zinc-700 bg-zinc-900')}
          >
            <SlidersHorizontal size={13} />
            Filters
          </button>
          <button onClick={() => void handleRefresh()} className="btn text-xs gap-1.5">
            <RefreshCw size={13} className={cn((loading || dashLoading) && 'animate-spin-slow')} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-2.5 section-block">
        {statCards.map((s) => (
          <div key={s.label} className="rounded-lg border border-zinc-800 bg-zinc-950 p-2.5">
            <p className="mb-1 text-2xs uppercase tracking-wider text-zinc-500">{s.label}</p>
            <p className="text-2xl font-semibold tabular-nums text-zinc-100">{s.value}</p>
            <p className="mt-0.5 text-2xs text-zinc-500">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Filters panel */}
      {filterOpen && (
        <div className="card p-3.5 mb-4 animate-slide-up">
          <p className="mb-3 text-xs font-medium text-zinc-300">Filter jobs</p>
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6">
            <label className="flex items-center gap-2 text-xs text-zinc-300">
              Min fit score
              <select
                className="field w-24 text-xs py-1"
                value={minFit}
                onChange={(e) => setMinFit(Number(e.target.value))}
              >
                <option value={0}>Any</option>
                <option value={3}>3.0+</option>
                <option value={3.5}>3.5+</option>
                <option value={4}>4.0+</option>
                <option value={4.5}>4.5+</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs text-zinc-300">
              <Globe size={12} />
              Location
              <input className="field w-32 text-xs py-1" placeholder="e.g. Remote" />
            </label>
          </div>
        </div>
      )}

      {/* Job list */}
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Top matches · {filteredJobs.length} shown
        </p>
      </div>

      <div className="space-y-3">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <JobSkeleton key={i} />)
          : filteredJobs.length === 0 && onboarding?.state === 'no_resume'
          ? (
            <div className="card p-6 sm:p-8 text-zinc-300">
              <div className="mx-auto max-w-2xl text-center">
                <div className="mb-3 inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-2xs font-medium text-amber-200">
                  No resume connected
                </div>
                <p className="text-lg font-medium text-zinc-100">No jobs yet — upload your resume to start matching.</p>
                <p className="mt-2 text-sm text-zinc-400">
                  Daubo scores your fit across tech, culture, seniority, comp, and location before showing jobs.
                </p>
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                  <Link href="/resume" className="btn btn-primary text-xs">Upload Resume</Link>
                  <Link href="/resume" className="btn text-xs">How matching works</Link>
                </div>
              </div>
            </div>
          )
          : filteredJobs.length === 0 && onboarding?.state === 'scoring_in_progress'
          ? (
            <div className="card p-6 sm:p-8">
              <div className="mx-auto max-w-2xl">
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <span className="badge bg-amber-500/15 text-amber-200 border-amber-500/30 text-2xs">Scoring in progress</span>
                  {etaMinutes != null && (
                    <span className="badge text-2xs border-zinc-700 text-zinc-300"><Timer size={10} /> ~{etaMinutes} min</span>
                  )}
                </div>
                <p className="text-lg font-medium text-zinc-100">Great — your resume is uploaded.</p>
                <p className="mt-1 text-sm text-zinc-400">
                  We are scoring your first set of jobs now. This usually takes about 1-2 minutes.
                </p>
                <div className="mt-5 space-y-2">
                  {onboardingSteps.map((step) => {
                    const active = onboarding.current_step === step
                    const done = onboardingSteps.indexOf(onboarding.current_step as typeof onboardingSteps[number]) > onboardingSteps.indexOf(step)
                    return (
                      <div key={step} className="flex items-center justify-between rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2">
                        <span className={cn('text-xs', active ? 'text-zinc-100' : 'text-zinc-400')}>{ONBOARDING_STEP_LABELS[step]}</span>
                        <span className={cn('text-2xs', done ? 'text-emerald-300' : active ? 'text-amber-200' : 'text-zinc-500')}>
                          {done ? 'Done' : active ? 'In progress' : 'Pending'}
                        </span>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 flex items-start gap-2 rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-xs text-zinc-400">
                  <ShieldCheck size={13} className="mt-0.5 text-emerald-300" />
                  You can leave this page. We keep processing in the background.
                </div>
              </div>
            </div>
          )
          : filteredJobs.length === 0
          ? (
            <div className="py-16 text-center text-zinc-500">
              <Globe size={28} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm font-medium text-zinc-300">No matches yet</p>
              <p className="text-xs mt-1">Upload your resume and click Refresh to discover roles</p>
            </div>
          )
          : filteredJobs.map((job) => <JobCard key={job.id} job={job} />)
        }
      </div>
    </div>
  )
}
