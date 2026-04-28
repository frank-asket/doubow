'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import useSWR from 'swr'
import { AlertTriangle, ArrowLeft, Loader2, Send, X } from 'lucide-react'

import { ApiError, applicationsApi, approvalsApi, jobsApi } from '@/lib/api'
import { candidatePageShell, candidateTokens } from '@/lib/candidateUi'
import { dashboardUi } from '@/lib/dashboardUi'
import { relativeTime, scoreBarWidth } from '@/lib/utils'
import type { Approval, JobWithScore } from '@doubow/shared'

const DIMENSION_LABELS: Record<string, string> = {
  tech: 'Technical stack',
  culture: 'Culture',
  seniority: 'Seniority',
  comp: 'Compensation',
  location: 'Location',
}
const SURFACE_BORDER = 'rgba(109,122,119,0.45)'

async function fetchJobById(jobId: string): Promise<JobWithScore | null> {
  const pagesToScan = [1, 2, 3, 4, 5]
  for (const page of pagesToScan) {
    const res = await jobsApi.list({ page })
    const found = res.items.find((j) => j.id === jobId)
    if (found) return found
    if (res.items.length === 0) break
  }
  return null
}

export default function JobDetailPage() {
  const params = useParams<{ jobId: string }>()
  const jobId = params.jobId
  const [approval, setApproval] = useState<Approval | null>(null)
  const [draftBody, setDraftBody] = useState('')
  const [loadingDraft, setLoadingDraft] = useState(false)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [actionState, setActionState] = useState<'idle' | 'approved' | 'rejected'>('idle')
  const [actionError, setActionError] = useState<string | null>(null)

  const { data: job, isLoading, error } = useSWR(
    jobId ? ['job-detail', jobId] : null,
    () => fetchJobById(jobId),
  )
  const createIdempotencyKey = useMemo(
    () => (job ? `job_detail_${job.id}_${job.score.channel_recommendation}` : ''),
    [job],
  )
  const fallbackDraft = useMemo(
    () =>
      job
        ? `Hello ${job.company} team,\n\nI am excited about the ${job.title} role and the opportunity to contribute based on my background.\n\nBest,\n[Your Name]`
        : '',
    [job],
  )

  useEffect(() => {
    if (!job) return
    setActionError(null)
    setActionState('idle')
    setApproval(null)
    setDraftBody(fallbackDraft)
  }, [job, fallbackDraft])

  async function ensureDraftApproval(): Promise<Approval | null> {
    if (!job) return null
    if (approval) return approval
    setLoadingDraft(true)
    setActionError(null)
    try {
      const app = await applicationsApi.create(job.id, job.score.channel_recommendation, {
        idempotencyKey: createIdempotencyKey,
      })
      const next = await applicationsApi.createDraft(app.id)
      setApproval(next)
      setDraftBody(next.draft_body)
      return next
    } catch (e) {
      if (e instanceof ApiError) {
        setActionError(e.detail || 'Could not prepare this outreach draft.')
      } else {
        setActionError('Could not prepare this outreach draft.')
      }
      return null
    } finally {
      setLoadingDraft(false)
    }
  }

  async function handleApprove() {
    if (approving || rejecting) return
    setApproving(true)
    setActionError(null)
    try {
      const current = await ensureDraftApproval()
      if (!current) return
      await approvalsApi.approve(current.id, draftBody)
      setActionState('approved')
    } catch (e) {
      if (e instanceof ApiError) {
        setActionError(e.detail || 'Could not approve and queue this draft.')
      } else {
        setActionError('Could not approve and queue this draft.')
      }
    } finally {
      setApproving(false)
    }
  }

  async function handleReject() {
    if (approving || rejecting) return
    setRejecting(true)
    setActionError(null)
    try {
      const current = await ensureDraftApproval()
      if (!current) return
      await approvalsApi.reject(current.id)
      setActionState('rejected')
      setApproval(null)
    } catch (e) {
      if (e instanceof ApiError) {
        setActionError(e.detail || 'Could not reject this draft.')
      } else {
        setActionError('Could not reject this draft.')
      }
    } finally {
      setRejecting(false)
    }
  }

  return (
    <div className={candidatePageShell}>
      <div className="mb-1">
        <Link href="/discover" className="inline-flex items-center gap-1 text-xs font-medium text-zinc-500 hover:text-zinc-800 dark:font-bold dark:text-white dark:hover:text-white">
          <ArrowLeft size={12} />
          Back to catalog
        </Link>
      </div>

      {isLoading ? (
        <section className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-4" style={{ borderColor: SURFACE_BORDER }}>
          <p className="text-sm text-zinc-500 dark:font-bold dark:text-white">Loading job detail...</p>
        </section>
      ) : error || !job ? (
        <section className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-4" style={{ borderColor: SURFACE_BORDER }}>
          <div className="flex items-center gap-2 text-rose-700">
            <AlertTriangle size={14} />
            Could not load this role.
          </div>
        </section>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          <section className="space-y-4 lg:col-span-8">
            <article className={dashboardUi.utilityCard} style={{ borderColor: SURFACE_BORDER }}>
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 items-center justify-center border border-[0.5px] bg-zinc-50 text-xs font-bold text-zinc-700 dark:text-white" style={{ borderColor: SURFACE_BORDER }}>
                  {job.company.slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight text-zinc-900 dark:font-bold dark:text-white">{job.title}</h1>
                    <span className="rounded bg-[#89f5e7] px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-[#005049]">
                      Open
                    </span>
                  </div>
                  <p className="text-sm text-zinc-600 dark:font-bold dark:text-white">{job.company} • {job.location || 'Location TBD'}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="rounded-sm border border-[0.5px] bg-zinc-50 px-2 py-1 text-xs text-zinc-600 dark:font-bold dark:text-white" style={{ borderColor: SURFACE_BORDER }}>
                      {job.salary_range || 'Salary not listed'}
                    </span>
                    <span className="rounded-sm border border-[0.5px] bg-zinc-50 px-2 py-1 text-xs text-zinc-600 dark:font-bold dark:text-white" style={{ borderColor: SURFACE_BORDER }}>
                      Posted {relativeTime(job.posted_at ?? job.discovered_at)}
                    </span>
                  </div>
                </div>
              </div>
            </article>

            <article className={dashboardUi.utilityCard} style={{ borderColor: SURFACE_BORDER }}>
              <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500 dark:font-bold dark:text-white">Job description</h2>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-700 dark:font-bold dark:text-white">
                {job.description || 'No description provided for this role.'}
              </p>
            </article>

            <article className={dashboardUi.utilityCard} style={{ borderColor: SURFACE_BORDER }}>
              <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500 dark:font-bold dark:text-white">Why Doubow matched this</h2>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {job.score.fit_reasons.slice(0, 4).map((reason, i) => (
                  <div key={i} className="rounded-sm border border-[0.5px] bg-zinc-50 p-3" style={{ borderColor: SURFACE_BORDER }}>
                    <p className="text-sm text-zinc-700 dark:font-bold dark:text-white">{reason}</p>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <aside className="space-y-4 lg:col-span-4">
            <article className={dashboardUi.utilityCard} style={{ borderColor: SURFACE_BORDER }}>
              <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500 dark:font-bold dark:text-white">Match analytics</h2>
              <div className="space-y-3">
                {Object.entries(job.score.dimension_scores).map(([key, value]) => (
                  <div key={key}>
                    <div className="mb-1 flex items-end justify-between">
                      <span className="text-xs font-semibold text-zinc-800 dark:font-bold dark:text-white">{DIMENSION_LABELS[key] ?? key}</span>
                      <span className="text-[11px] font-semibold text-teal-700">{Math.round(scoreBarWidth(value))}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-100">
                      <div className="h-full bg-teal-600" style={{ width: `${scoreBarWidth(value)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-2xl border border-[0.5px] bg-white shadow-sm dark:bg-slate-900 lg:sticky lg:top-20" style={{ borderColor: SURFACE_BORDER }}>
              <div className="border-b border-[0.5px] bg-zinc-50 px-4 py-4" style={{ borderColor: SURFACE_BORDER }}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500 dark:font-bold dark:text-white">Draft workspace</p>
                  <span className="rounded-full border border-zinc-200 bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-zinc-600 dark:font-bold dark:text-white">
                    human review
                  </span>
                </div>
                <p className="mt-1 text-sm font-medium text-zinc-800 dark:font-bold dark:text-white">Subject: Interest in {job.title}</p>
              </div>
              <div className="p-4">
                <textarea
                  value={draftBody}
                  onFocus={() => {
                    if (!approval && !loadingDraft) void ensureDraftApproval()
                  }}
                  onChange={(e) => {
                    setDraftBody(e.target.value)
                    if (actionState !== 'idle') setActionState('idle')
                  }}
                  className="h-56 w-full resize-none rounded-xl border border-[0.5px] p-4 text-sm leading-relaxed text-zinc-700 outline-none focus:border-teal-600 dark:font-bold dark:text-white"
                  style={{ borderColor: SURFACE_BORDER }}
                />
              </div>
              <div className="mx-4 mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                <AlertTriangle size={dashboardUi.actionIcon} className="mt-0.5 text-amber-700" />
                <p className="text-xs leading-snug text-amber-900">
                  Human-in-the-loop: review this draft before sequence initiation.
                </p>
              </div>
              {actionError ? (
                <p className="mx-4 mb-3 text-xs font-medium text-rose-700">{actionError}</p>
              ) : null}
              {actionState === 'approved' ? (
                <div className="mx-4 mb-3 flex items-center justify-between gap-2 rounded-sm border border-emerald-200 bg-emerald-50 p-2">
                  <p className="text-xs font-medium text-emerald-700">
                    Outreach approved and queued. Continue in approvals.
                  </p>
                  {approval ? (
                    <Link
                      href={`/approvals?approvalId=${encodeURIComponent(approval.id)}`}
                  className={`${dashboardUi.actionButton} rounded-lg border border-emerald-300 bg-white dark:bg-slate-900 text-emerald-700 hover:bg-emerald-100`}
                    >
                      Open in Approvals
                    </Link>
                  ) : null}
                </div>
              ) : null}
              {actionState === 'rejected' ? (
                <p className="mx-4 mb-3 text-xs font-medium text-zinc-600 dark:font-bold dark:text-white">
                  Draft rejected. Generate or edit a new one any time.
                </p>
              ) : null}
              <div className="grid grid-cols-2 gap-2 border-t border-[0.5px] p-4" style={{ borderColor: SURFACE_BORDER }}>
                <button
                  onClick={() => void handleReject()}
                  disabled={approving || rejecting || loadingDraft}
                  className={`${dashboardUi.actionButton} border border-rose-300 text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-70`}
                >
                  {rejecting || loadingDraft ? <Loader2 size={dashboardUi.actionIcon} className="animate-spin" /> : <X size={dashboardUi.actionIcon} />}
                  {rejecting ? 'Rejecting...' : 'Reject'}
                </button>
                <button
                  onClick={() => void handleApprove()}
                  disabled={approving || rejecting || loadingDraft}
                  className={`${dashboardUi.actionButton} bg-teal-600 text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-70`}
                >
                  {approving || loadingDraft ? <Loader2 size={dashboardUi.actionIcon} className="animate-spin" /> : <Send size={dashboardUi.actionIcon} />}
                  {approving ? 'Queuing...' : 'Approve outreach'}
                </button>
              </div>
            </article>
          </aside>
        </div>
      )}
    </div>
  )
}

