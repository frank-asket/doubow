'use client'

import { CalendarDays, ChevronRight, ClipboardList, Ellipsis, SearchCheck } from 'lucide-react'
import Link from 'next/link'
import useSWR from 'swr'
import { useAuth } from '@clerk/nextjs'
import { useDashboard } from '@/hooks/useDashboard'
import { applicationsApi } from '@/lib/api'
import { isE2EAuthBypass } from '@/lib/e2e'
import type { Application } from '@/types'
import { formatApplicationStatus } from '@/components/dashboard/dashboardCopy'

function sortApplicationsRecent(items: Application[]) {
  return [...items].sort(
    (a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime(),
  )
}

export default function DashboardOverviewPage() {
  const { summary, loading: summaryLoading, error: summaryError } = useDashboard()
  const { isLoaded, isSignedIn } = useAuth()
  const ready = isE2EAuthBypass() || (isLoaded && isSignedIn)

  const { data: allApplications, error: appsError, isLoading: appsLoading } = useSWR(
    ready ? 'dashboard-overview-applications' : null,
    async () => {
      const res = await applicationsApi.list()
      return res.items
    },
    { shouldRetryOnError: false, errorRetryCount: 0 },
  )

  const recentApplications = allApplications ? sortApplicationsRecent(allApplications).slice(0, 5) : []
  const savedApplications = allApplications
    ? allApplications.filter((a) => a.status === 'saved').slice(0, 5)
    : []

  const nextInterviewApp = allApplications
    ? sortApplicationsRecent(allApplications.filter((a) => a.status === 'interview'))[0]
    : undefined

  const pipelineCount = summary?.pipeline_count ?? 0
  const pendingApprovals = summary?.pending_approvals ?? 0
  const highFit = summary?.high_fit_count ?? 0
  const evaluatedWeek = summary?.evaluated_this_week ?? 0
  const avgFit = summary?.avg_fit_score
  const awaitingReply = summary?.applied_awaiting_reply ?? 0
  const scoredTotal = summary?.total_scored_jobs ?? 0

  const awaitingSlice =
    pipelineCount > 0 ? Math.min(awaitingReply, pipelineCount) : 0
  const awaitingDeg =
    pipelineCount > 0 ? Math.round((awaitingSlice / pipelineCount) * 360) : 0
  const restDeg = Math.max(0, 360 - awaitingDeg)

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-[28px] font-semibold leading-none tracking-[-0.02em] text-zinc-900 sm:text-[34px]">
            Dashboard
          </h1>
          <p className="mt-2 max-w-xl text-[15px] text-zinc-500">
            Here&apos;s how your job search looks this month—numbers come from your workspace when the API is
            available.
          </p>
        </div>
        <button
          type="button"
          className="inline-flex shrink-0 items-center gap-2 self-start rounded-[10px] border border-[#e4e5ec] bg-white px-3 py-2 text-[14px] font-medium text-zinc-700 shadow-sm"
        >
          <CalendarDays size={15} />
          This Month
        </button>
      </header>

      {summaryError ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] text-amber-950">
          Dashboard stats couldn&apos;t load. Check that the backend is running and NEXT_PUBLIC_API_URL is correct.
        </div>
      ) : null}

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <article className="rounded-[16px] border border-[#e7e8ee] bg-[radial-gradient(circle_at_top_left,_#efefff,_#f9f9ff_45%,_#ffffff)] p-6">
          <div className="flex flex-wrap items-start gap-8 sm:gap-10">
            <div className="space-y-2">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white shadow-sm">
                <ClipboardList size={18} />
              </span>
              <p className="text-[44px] font-semibold leading-none tracking-[-0.02em] text-zinc-900 sm:text-[52px]">
                {summaryLoading ? '…' : pipelineCount}
              </p>
              <p className="text-[14px] text-zinc-500">In pipeline</p>
            </div>
            <div className="space-y-2">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-amber-200 text-amber-800 shadow-sm">
                <SearchCheck size={18} />
              </span>
              <p className="text-[44px] font-semibold leading-none tracking-[-0.02em] text-zinc-900 sm:text-[52px]">
                {summaryLoading ? '…' : pendingApprovals}
              </p>
              <p className="text-[14px] text-zinc-500">Pending approvals</p>
            </div>
          </div>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <h2 className="text-lg font-semibold tracking-tight text-zinc-900 sm:text-xl">Pipeline snapshot</h2>
          <p className="mt-1 text-sm text-zinc-500">Derived from your dashboard summary</p>
          <div className="mt-4 flex items-center gap-5">
            <div
              className="h-[88px] w-[88px] shrink-0 rounded-full sm:h-[104px] sm:w-[104px]"
              style={{
                background:
                  pipelineCount > 0
                    ? `conic-gradient(#2f45ce 0deg ${awaitingDeg}deg, #eef0f5 ${awaitingDeg}deg ${awaitingDeg + restDeg}deg)`
                    : 'conic-gradient(#eef0f5 0deg 360deg)',
              }}
            >
              <div className="m-3 h-[calc(100%-24px)] w-[calc(100%-24px)] rounded-full bg-white sm:m-[14px] sm:h-[76px] sm:w-[76px]" />
            </div>
            <div className="min-w-0 space-y-2 text-[13px] text-zinc-600">
              <p>
                <span className="mr-2 inline-block h-2 w-2 rounded-full bg-indigo-600" />
                Applied, awaiting reply:{' '}
                <span className="font-semibold tabular-nums text-zinc-900">{awaitingReply}</span>
              </p>
              <p>
                <span className="mr-2 inline-block h-2 w-2 rounded-full bg-zinc-300" />
                Other pipeline:{' '}
                <span className="font-semibold tabular-nums text-zinc-900">
                  {Math.max(0, pipelineCount - awaitingSlice)}
                </span>
              </p>
              {pipelineCount === 0 ? (
                <p className="text-zinc-500">Save or queue roles from Discover to build your pipeline.</p>
              ) : null}
            </div>
          </div>
          <dl className="mt-5 grid gap-2 border-t border-zinc-100 pt-4 text-[13px]">
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Evaluated this week</dt>
              <dd className="font-medium tabular-nums text-zinc-900">{evaluatedWeek}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Avg fit score</dt>
              <dd className="font-medium tabular-nums text-zinc-900">
                {avgFit != null ? avgFit.toFixed(1) : '—'}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Scored jobs (total)</dt>
              <dd className="font-medium tabular-nums text-zinc-900">{scoredTotal}</dd>
            </div>
          </dl>
          <Link
            href="/pipeline"
            className="mt-4 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700"
          >
            View pipeline <ChevronRight size={14} />
          </Link>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold tracking-tight text-zinc-900 sm:text-xl">Next interview</h2>
          </div>
          <p className="mt-1 text-sm text-zinc-500">From applications marked interview</p>
          {nextInterviewApp ? (
            <>
              <div className="mt-4 rounded-[12px] border border-indigo-200 bg-indigo-50/50 p-3">
                <p className="text-[14px] font-semibold text-zinc-800">{nextInterviewApp.job.title}</p>
                <p className="mt-1 text-[12px] text-zinc-500">{nextInterviewApp.job.company}</p>
              </div>
              <Link
                href="/prep"
                className="mt-5 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700"
              >
                Interview prep <ChevronRight size={14} />
              </Link>
            </>
          ) : (
            <p className="mt-4 text-sm text-zinc-600">
              No interview-stage applications yet. Move a role to interview in{' '}
              <Link href="/pipeline" className="font-semibold text-indigo-700 hover:underline">
                Pipeline
              </Link>
              .
            </p>
          )}
        </article>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold tracking-tight text-zinc-900 sm:text-xl">
              Recent applications
            </h3>
            <Ellipsis size={18} className="text-zinc-400" aria-hidden />
          </div>
          {appsError ? (
            <p className="text-sm text-rose-600">Could not load applications.</p>
          ) : appsLoading ? (
            <p className="text-sm text-zinc-500">Loading…</p>
          ) : recentApplications.length === 0 ? (
            <p className="text-sm text-zinc-600">
              Nothing yet.{' '}
              <Link href="/discover" className="font-semibold text-indigo-700 hover:underline">
                Discover roles
              </Link>{' '}
              and add them to your pipeline.
            </p>
          ) : (
            <div className="space-y-4">
              {recentApplications.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-3 border-b border-zinc-200/70 pb-3 last:border-0"
                >
                  <div className="min-w-0">
                    <p className="text-[15px] font-semibold text-zinc-800">{item.job.title}</p>
                    <p className="text-[12px] text-zinc-500">{item.job.company}</p>
                  </div>
                  <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-1 text-[12px] text-zinc-700">
                    {formatApplicationStatus(item.status)}
                  </span>
                </div>
              ))}
            </div>
          )}
          <Link
            href="/pipeline"
            className="mt-4 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700"
          >
            All applications <ChevronRight size={14} />
          </Link>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold tracking-tight text-zinc-900 sm:text-xl">Saved jobs</h3>
            <Ellipsis size={18} className="text-zinc-400" aria-hidden />
          </div>
          {appsError ? (
            <p className="text-sm text-rose-600">Could not load saved jobs.</p>
          ) : appsLoading ? (
            <p className="text-sm text-zinc-500">Loading…</p>
          ) : savedApplications.length === 0 ? (
            <p className="text-sm text-zinc-600">
              No saved roles. Star or save jobs from{' '}
              <Link href="/discover" className="font-semibold text-indigo-700 hover:underline">
                Discover
              </Link>
              .
            </p>
          ) : (
            <div className="space-y-4">
              {savedApplications.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-3 border-b border-zinc-200/70 pb-3 last:border-0"
                >
                  <p className="min-w-0 text-[15px] font-semibold text-zinc-800">{item.job.title}</p>
                  <span className="shrink-0 text-[12px] text-zinc-500">{item.job.company}</span>
                </div>
              ))}
            </div>
          )}
          <Link
            href="/discover"
            className="mt-4 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700"
          >
            Discover more <ChevronRight size={14} />
          </Link>
        </article>
      </section>

      <section className="rounded-[14px] border border-indigo-100 bg-indigo-50/70 p-4">
        <p className="text-[14px] text-indigo-900">
          High-fit opportunities in your queue:{' '}
          <span className="font-semibold tabular-nums">{summaryLoading ? '…' : highFit}</span>
        </p>
      </section>
    </div>
  )
}
