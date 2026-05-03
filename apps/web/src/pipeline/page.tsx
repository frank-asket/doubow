'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useState } from 'react'
import type { Route } from 'next'
import { AlertTriangle, RefreshCw, Loader2, FileEdit } from 'lucide-react'
import { DashboardPageHeader } from '../../components/dashboard/DashboardPageHeader'
import { MatchPipelineUpdateCard } from '../../components/dashboard/MatchPipelineUpdateCard'
import { cn, statusBadgeClass, channelBadgeClass, channelLabel, shortDate, fitClass } from '../../lib/utils'
import { usePipeline } from './usePipeline'
import { usePipelineStore } from './pipelineStore'
import { ApiError, applicationsApi } from '../../lib/api'
import type { Application, ApplicationStatus, IntegrityChange } from '@doubow/shared'
import { INTEGRITY_CHANGE_LABELS, PIPELINE_STATUS_TABS, PIPELINE_TABLE_HEADERS } from './constants'
import { hasPipelineIntegrityIssues } from './helpers'
import { candidatePageShell, candidateTokens } from '../../lib/candidateUi'
import { motion, useReducedMotion, fadeInUpVariants, staggerContainerVariants, getMicroInteractionMotion } from '../../lib/motion'

function ChangeRow({
  change,
  onJumpToApplication,
}: {
  change: IntegrityChange
  onJumpToApplication: (applicationId: string) => void
}) {
  const label = INTEGRITY_CHANGE_LABELS[change.type]
  const targetId = change.application_ids[0]
  const canJump = Boolean(targetId)

  return (
    <div className="flex items-start gap-3 border-b border-zinc-100 py-2.5 last:border-0">
      <span className={cn(
        'badge text-2xs mt-0.5',
        change.type === 'deduplicate' ? 'badge-interview' :
        change.type === 'mark_stale' ? 'badge-pending' : 'badge-applied'
      )}>
        {label}
      </span>
      <p className="flex-1 text-xs text-zinc-600">{change.reason}</p>
      <button
        type="button"
        disabled={!canJump}
        onClick={() => {
          if (targetId) onJumpToApplication(targetId)
        }}
        className="text-2xs whitespace-nowrap text-primary-green hover:underline disabled:cursor-not-allowed disabled:opacity-40"
      >
        Jump to row
      </button>
    </div>
  )
}

export default function PipelinePage() {
  const router = useRouter()
  const { applications, integrityResult, integrityLoading, setIntegrityResult, setIntegrityLoading } = usePipelineStore()
  const { refresh } = usePipeline()
  const [activeTab, setActiveTab] = useState<ApplicationStatus | 'all'>('all')
  const [applying, setApplying] = useState(false)
  const [draftingId, setDraftingId] = useState<string | null>(null)
  const [draftError, setDraftError] = useState<string | null>(null)
  const [draftSuccess, setDraftSuccess] = useState<string | null>(null)
  const prefersReducedMotion = useReducedMotion()
  const motionEnabled = !prefersReducedMotion
  const microInteractionMotion = getMicroInteractionMotion(motionEnabled)

  async function generateDraft(app: Application) {
    setDraftError(null)
    setDraftingId(app.id)
    try {
      const approval = await applicationsApi.createDraft(app.id)
      await refresh()
      setDraftSuccess('Draft ready - opening Approvals...')
      await new Promise((resolve) => setTimeout(resolve, 450))
      router.push(`/approvals?approvalId=${encodeURIComponent(approval.id)}`)
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setDraftError(
          'That application was not found for your account—try Refresh, or add the role again from Discover.',
        )
      } else if (e instanceof ApiError) {
        setDraftError(e.detail || 'Could not generate draft.')
      } else {
        setDraftError('Could not generate draft.')
      }
    } finally {
      setDraftingId(null)
    }
  }

  const filtered = activeTab === 'all'
    ? applications
    : applications.filter((a) => a.status === activeTab)
  const interviewCount = applications.filter((a) => a.status === 'interview').length
  const staleCount = applications.filter((a) => a.is_stale).length
  const avgFit = applications.length
    ? applications.reduce((sum, app) => sum + (app.score?.fit_score ?? 0), 0) / applications.length
    : null

  async function runIntegrity(mode: 'dry_run' | 'apply') {
    if (mode === 'apply') setApplying(true)
    else setIntegrityLoading(true)
    try {
      const result = await applicationsApi.integrityCheck(mode)
      setIntegrityResult(result)
      if (mode === 'apply') refresh()
    } catch {
      // handle error
    } finally {
      setIntegrityLoading(false)
      setApplying(false)
    }
  }

  const hasIntegrityIssues = hasPipelineIntegrityIssues(applications)

  const jumpToApplicationRow = useCallback((applicationId: string) => {
    setActiveTab('all')
    window.requestAnimationFrame(() => {
      const el = document.querySelector<HTMLElement>(`[data-application-id="${applicationId}"]`)
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el?.classList.add('ring-2', 'ring-secondary-green/60', 'ring-offset-2', 'ring-offset-white', 'dark:ring-offset-slate-950')
      window.setTimeout(() => {
        el?.classList.remove('ring-2', 'ring-secondary-green/60', 'ring-offset-2', 'ring-offset-white', 'dark:ring-offset-slate-950')
      }, 1800)
    })
  }, [])

  return (
    <motion.div
      className={candidatePageShell}
      variants={motionEnabled ? staggerContainerVariants : undefined}
      initial={motionEnabled ? 'hidden' : false}
      animate={motionEnabled ? 'visible' : undefined}
    >
      {draftSuccess && (
        <div className="pointer-events-none fixed right-4 top-20 z-50 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-900 shadow-sm">
          {draftSuccess}
        </div>
      )}
      <DashboardPageHeader
        kicker="Applications"
        title="My applications"
        description="Manage your active recruitment pipelines and match scores."
        actions={
          <motion.button
            type="button"
            onClick={() => refresh()}
            {...microInteractionMotion}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[0.5px] bg-white dark:bg-slate-900 px-3 py-2 text-[14px] font-medium shadow-sm hover:bg-[#f0f5f2]"
            style={{ borderColor: candidateTokens.outline, color: candidateTokens.onSurface }}
          >
            <RefreshCw size={13} />
            Refresh
          </motion.button>
        }
      />

      <MatchPipelineUpdateCard onAfterRun={() => void refresh()} />

      <div
        className="flex flex-wrap items-center justify-between gap-2 rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 px-3 py-2"
        style={{ borderColor: 'rgba(109,122,119,0.45)' }}
      >
        <p className="text-2xs font-semibold uppercase tracking-wider text-zinc-500">
          Application Pipeline
        </p>
        <div className="inline-flex items-center overflow-hidden rounded-sm border border-[0.5px]" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
            <motion.button {...microInteractionMotion} className="bg-bg-light-green px-3 py-1.5 text-2xs font-semibold text-primary-green">List</motion.button>
          <motion.button {...microInteractionMotion} className="border-l border-[0.5px] px-3 py-1.5 text-2xs font-semibold text-zinc-500" style={{ borderColor: 'rgba(109,122,119,0.45)' }}>
            Kanban
          </motion.button>
        </div>
      </div>

      {draftError && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-[12px] border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-900"
        >
          <AlertTriangle size={16} className="mt-0.5 shrink-0 text-red-600" />
          <p className="flex-1">{draftError}</p>
          <button
            type="button"
            className="text-xs font-medium text-red-800 underline"
            onClick={() => setDraftError(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Integrity banner */}
      {hasIntegrityIssues && !integrityResult && (
        <div className="mb-5 flex items-start gap-3 rounded-[16px] border border-amber-200 bg-amber-50 p-3.5 animate-fade-in">
          <AlertTriangle size={15} className="mt-0.5 flex-shrink-0 text-amber-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-950">Integrity issues detected</p>
            <p className="mt-0.5 text-xs text-amber-800">Possible duplicates and stale entries found</p>
          </div>
          <div className="flex items-center gap-2">
            <motion.button
              type="button"
              onClick={() => runIntegrity('dry_run')}
              disabled={integrityLoading}
              {...microInteractionMotion}
              className="inline-flex items-center gap-1 rounded-[10px] border border-amber-300 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-medium text-amber-950 shadow-sm hover:bg-amber-100 disabled:opacity-50"
            >
              {integrityLoading ? <Loader2 size={12} className="animate-spin" /> : null}
              Preview cleanup
            </motion.button>
          </div>
        </div>
      )}

      {/* Integrity result */}
      {integrityResult && (
        <div className="card p-4 mb-5 animate-slide-up">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div>
              <p className="text-sm font-medium text-zinc-900">Integrity check results</p>
              <p className="mt-0.5 text-xs text-zinc-500">
                {integrityResult.mode === 'dry_run' ? 'Preview — no changes applied yet' : 'Changes applied'}
              </p>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
              <span className="badge badge-pending text-xs">{integrityResult.summary.duplicates} dupes</span>
              <span className="badge badge-rejected text-xs">{integrityResult.summary.stale} stale</span>
              <span className="badge badge-applied text-xs">{integrityResult.summary.status_fixes} fixes</span>
            </div>
          </div>
          <div className="divide-y divide-zinc-100">
            {integrityResult.changes.map((c, i) => (
              <ChangeRow key={i} change={c} onJumpToApplication={jumpToApplicationRow} />
            ))}
          </div>
          {integrityResult.mode === 'dry_run' && (
            <div className="mt-3 flex gap-2 border-t border-zinc-100 pt-3">
              <button
                onClick={() => runIntegrity('apply')}
                disabled={applying}
                className="btn btn-primary text-xs"
              >
                {applying ? <Loader2 size={12} className="animate-spin" /> : null}
                Apply all changes
              </button>
              <button onClick={() => setIntegrityResult(null)} className="btn text-xs">
                Dismiss
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tabs — mock: Active / Archived / Drafts segmented control */}
      <div
        className="mb-4 flex w-full gap-0 overflow-x-auto rounded border border-[0.5px] bg-[#f0f5f2] p-1 sm:w-fit"
        style={{ borderColor: candidateTokens.outline }}
      >
        {PIPELINE_STATUS_TABS.map((tab) => {
          const count = tab.value === 'all'
            ? applications.length
            : applications.filter((a) => a.status === tab.value).length
          return (
            <motion.button
              key={tab.value}
              type="button"
              onClick={() => setActiveTab(tab.value)}
              {...microInteractionMotion}
              className={cn(
                'rounded-md border-[0.5px] px-3 py-1.5 text-xs font-medium transition-all duration-150',
                activeTab === tab.value
                  ? 'border-primary-green/30 bg-white dark:bg-slate-900 font-semibold text-primary-green shadow-sm'
                  : 'border-transparent text-zinc-500 hover:bg-white dark:bg-slate-900/70 hover:text-zinc-800',
              )}
            >
              {tab.label}
              {count > 0 && (
                <span className="ml-1.5 text-2xs tabular-nums text-zinc-400">{count}</span>
              )}
            </motion.button>
          )
        })}
      </div>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <motion.article
          variants={motionEnabled ? fadeInUpVariants : undefined}
          className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-3 shadow-sm"
          style={{ borderColor: 'rgba(109,122,119,0.45)' }}
        >
          <p className="text-2xs uppercase tracking-wider text-zinc-500">In interview stage</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-900">{interviewCount}</p>
          <p className="mt-0.5 text-2xs text-zinc-500">Focus these first in prep</p>
        </motion.article>
        <motion.article
          variants={motionEnabled ? fadeInUpVariants : undefined}
          className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-3 shadow-sm"
          style={{ borderColor: 'rgba(109,122,119,0.45)' }}
        >
          <p className="text-2xs uppercase tracking-wider text-zinc-500">Average fit</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-900">
            {avgFit != null ? avgFit.toFixed(1) : '—'}
          </p>
          <p className="mt-0.5 text-2xs text-zinc-500">Across visible applications</p>
        </motion.article>
        <motion.article
          variants={motionEnabled ? fadeInUpVariants : undefined}
          className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-3 shadow-sm"
          style={{ borderColor: 'rgba(109,122,119,0.45)' }}
        >
          <p className="text-2xs uppercase tracking-wider text-zinc-500">Needs cleanup</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-900">{staleCount}</p>
          <p className="mt-0.5 text-2xs text-zinc-500">Stale records flagged</p>
        </motion.article>
      </section>

      {/* Table */}
      <div
        className="overflow-x-auto border-[0.5px] bg-white dark:bg-slate-900 shadow-sm"
        style={{ borderColor: candidateTokens.outline }}
      >
        <table className="w-full min-w-[760px]">
          <thead>
            <tr className="border-b border-[0.5px] bg-[#f0f5f2]" style={{ borderColor: candidateTokens.outline }}>
              {PIPELINE_TABLE_HEADERS.map((h) => (
                <th
                  key={h}
                  className="px-4 py-2.5 text-left text-[11px] font-normal uppercase tracking-tight"
                  style={{ color: candidateTokens.onVariant }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-xs text-zinc-500">
                  No applications in this category yet
                </td>
              </tr>
            ) : (
              filtered.map((app) => (
                <tr
                  key={app.id}
                  data-application-id={app.id}
                  className="group scroll-mt-24 border-b border-[0.5px] transition-colors hover:bg-[#f5faf8]"
                  style={{ borderColor: candidateTokens.outline }}
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded border border-secondary-green/20 bg-bg-light-green text-2xs font-semibold text-primary-green">
                        {app.job.company.slice(0, 2).toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-zinc-900">{app.job.company}</span>
                      {app.is_stale && (
                        <span className="rounded-full border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-2xs text-amber-900">
                          stale
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="max-w-[180px] truncate px-4 py-3 text-sm text-zinc-700">{app.job.title}</td>
                  <td className="py-3 px-4">
                    {app.score && (
                      <span className={cn('badge text-xs', fitClass(app.score.fit_score))}>
                        {app.score.fit_score.toFixed(1)}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className={cn('badge text-xs', channelBadgeClass(app.channel))}>
                      {channelLabel(app.channel)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={cn('badge text-xs', statusBadgeClass(app.status))}>
                      {app.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs tabular-nums text-zinc-500">
                    {shortDate(app.last_updated)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="inline-flex items-center gap-1.5">
                      <motion.button
                        type="button"
                        onClick={() => generateDraft(app)}
                        disabled={draftingId === app.id}
                        title="Generate outreach draft (opens in Approvals)"
                        {...microInteractionMotion}
                        className="inline-flex items-center gap-1 rounded-lg border border-[0.5px] bg-white dark:bg-slate-900 px-2 py-1 text-2xs font-medium shadow-sm hover:border-secondary-green/45 hover:bg-bg-light-green hover:text-primary-green disabled:opacity-50"
                        style={{ borderColor: candidateTokens.outline, color: candidateTokens.onSurface }}
                      >
                        {draftingId === app.id ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <FileEdit size={12} />
                        )}
                        Draft
                      </motion.button>
                      <motion.div {...microInteractionMotion}>
                        <Link
                        href={`/prep?applicationId=${encodeURIComponent(app.id)}` as Route}
                        className="inline-flex items-center rounded-lg border border-[0.5px] bg-white dark:bg-slate-900 px-2 py-1 text-2xs font-medium shadow-sm hover:border-secondary-green/45 hover:bg-bg-light-green hover:text-primary-green"
                        style={{ borderColor: candidateTokens.outline, color: candidateTokens.onSurface }}
                      >
                        Prep
                      </Link>
                      </motion.div>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
