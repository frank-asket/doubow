'use client'

import { useState } from 'react'
import { AlertTriangle, RefreshCw, Loader2, FileEdit } from 'lucide-react'
import { DashboardPageHeader } from '@/components/dashboard/DashboardPageHeader'
import { cn, statusBadgeClass, channelBadgeClass, channelLabel, shortDate, fitClass } from '@/lib/utils'
import { usePipeline } from '@/hooks/usePipeline'
import { usePipelineStore } from '@/stores/pipelineStore'
import { ApiError, applicationsApi } from '@/lib/api'
import type { Application, ApplicationStatus, IntegrityChange } from '@/types'

const STATUS_TABS: { label: string; value: ApplicationStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Applied', value: 'applied' },
  { label: 'Interview', value: 'interview' },
  { label: 'Pending', value: 'pending' },
  { label: 'Rejected', value: 'rejected' },
]

function ChangeRow({ change }: { change: IntegrityChange }) {
  const label = {
    deduplicate: '⊕ Deduplicate',
    mark_stale: '⏱ Mark stale',
    normalize_status: '↻ Normalize status',
  }[change.type]

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
      <button type="button" className="text-2xs whitespace-nowrap text-indigo-700 hover:underline">
        Jump to row
      </button>
    </div>
  )
}

export default function PipelinePage() {
  const { applications, integrityResult, integrityLoading, setIntegrityResult, setIntegrityLoading } = usePipelineStore()
  const { refresh } = usePipeline()
  const [activeTab, setActiveTab] = useState<ApplicationStatus | 'all'>('all')
  const [applying, setApplying] = useState(false)
  const [draftingId, setDraftingId] = useState<string | null>(null)
  const [draftError, setDraftError] = useState<string | null>(null)

  async function generateDraft(app: Application) {
    setDraftError(null)
    setDraftingId(app.id)
    try {
      await applicationsApi.createDraft(app.id)
      await refresh()
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

  const hasIntegrityIssues = applications.some((a) => a.is_stale || a.dedup_group)

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <DashboardPageHeader
        kicker="Pipeline"
        title="Pipeline"
        description="Track and manage all your applications"
        actions={
          <button
            type="button"
            onClick={() => refresh()}
            className="inline-flex items-center gap-1.5 rounded-[10px] border border-[#e4e5ec] bg-white px-3 py-2 text-[14px] font-medium text-zinc-700 shadow-sm hover:bg-zinc-50"
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        }
      />

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
            <button
              type="button"
              onClick={() => runIntegrity('dry_run')}
              disabled={integrityLoading}
              className="inline-flex items-center gap-1 rounded-[10px] border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-950 shadow-sm hover:bg-amber-100 disabled:opacity-50"
            >
              {integrityLoading ? <Loader2 size={12} className="animate-spin" /> : null}
              Preview cleanup
            </button>
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
            {integrityResult.changes.map((c, i) => <ChangeRow key={i} change={c} />)}
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

      {/* Tabs */}
      <div className="mb-4 flex w-full gap-1 overflow-x-auto rounded-[12px] border border-[#e7e8ee] bg-white p-1 shadow-sm sm:w-fit">
        {STATUS_TABS.map((tab) => {
          const count = tab.value === 'all'
            ? applications.length
            : applications.filter((a) => a.status === tab.value).length
          return (
            <button
              key={tab.value}
              type="button"
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                'rounded-[10px] px-3 py-1.5 text-xs transition-all duration-150',
                activeTab === tab.value
                  ? 'border border-indigo-200 bg-indigo-50 font-medium text-indigo-800'
                  : 'text-zinc-500 hover:bg-zinc-50 hover:text-zinc-800',
              )}
            >
              {tab.label}
              {count > 0 && (
                <span className="ml-1.5 text-2xs tabular-nums text-zinc-400">{count}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[760px]">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50/80">
              {['Company', 'Role', 'Fit', 'Channel', 'Status', 'Last update', ''].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-2xs font-medium uppercase tracking-wider text-zinc-500">
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
                <tr key={app.id} className="group border-b border-zinc-100 transition-colors hover:bg-zinc-50/80">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded border border-indigo-100 bg-indigo-50 text-2xs font-semibold text-indigo-800">
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
                    {app.applied_at ? shortDate(app.applied_at) : '—'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => generateDraft(app)}
                      disabled={draftingId === app.id}
                      title="Generate outreach draft (opens in Approvals)"
                      className="inline-flex items-center gap-1 rounded-lg border border-[#e4e5ec] bg-white px-2 py-1 text-2xs font-medium text-zinc-700 shadow-sm hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-800 disabled:opacity-50"
                    >
                      {draftingId === app.id ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <FileEdit size={12} />
                      )}
                      Draft
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
