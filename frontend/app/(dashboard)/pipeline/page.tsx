'use client'

import { useState } from 'react'
import { AlertTriangle, ChevronRight, RefreshCw, Loader2 } from 'lucide-react'
import { cn, statusBadgeClass, channelBadgeClass, channelLabel, shortDate, fitClass } from '@/lib/utils'
import { usePipeline } from '@/hooks/usePipeline'
import { usePipelineStore } from '@/stores/pipelineStore'
import { applicationsApi } from '@/lib/api'
import type { ApplicationStatus, IntegrityChange } from '@/types'

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
    <div className="flex items-start gap-3 border-b border-zinc-800 py-2.5 last:border-0">
      <span className={cn(
        'badge text-2xs mt-0.5',
        change.type === 'deduplicate' ? 'badge-interview' :
        change.type === 'mark_stale' ? 'badge-pending' : 'badge-applied'
      )}>
        {label}
      </span>
      <p className="flex-1 text-xs text-zinc-300">{change.reason}</p>
      <button className="text-2xs whitespace-nowrap text-emerald-300 hover:underline">
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
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-3 rounded-3xl border border-zinc-800 bg-[#080808] p-5 sm:flex-row sm:items-start sm:p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Pipeline</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Pipeline</h1>
          <p className="mt-2 text-sm text-zinc-400 sm:text-base">Track and manage all your applications</p>
        </div>
        <button onClick={() => refresh()} className="btn text-xs gap-1.5 self-start sm:self-auto">
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>

      {/* Integrity banner */}
      {hasIntegrityIssues && !integrityResult && (
        <div className="mb-5 flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3.5 animate-fade-in">
          <AlertTriangle size={15} className="mt-0.5 flex-shrink-0 text-amber-300" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-200">Integrity issues detected</p>
            <p className="mt-0.5 text-xs text-amber-200/80">Possible duplicates and stale entries found</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => runIntegrity('dry_run')}
              disabled={integrityLoading}
              className="btn border-amber-500/30 bg-amber-500/10 text-xs text-amber-200 hover:bg-amber-500/20"
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
              <p className="text-sm font-medium text-zinc-100">Integrity check results</p>
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
          <div className="divide-y divide-zinc-800">
            {integrityResult.changes.map((c, i) => <ChangeRow key={i} change={c} />)}
          </div>
          {integrityResult.mode === 'dry_run' && (
            <div className="mt-3 flex gap-2 border-t border-zinc-800 pt-3">
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
      <div className="mb-4 flex w-full gap-1 overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-950 p-1 sm:w-fit">
        {STATUS_TABS.map((tab) => {
          const count = tab.value === 'all'
            ? applications.length
            : applications.filter((a) => a.status === tab.value).length
          return (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs transition-all duration-150',
                activeTab === tab.value
                  ? 'border border-emerald-500/30 bg-emerald-500/10 font-medium text-emerald-300'
                  : 'text-zinc-400 hover:text-zinc-200'
              )}
            >
              {tab.label}
              {count > 0 && (
                <span className="ml-1.5 text-2xs tabular-nums text-zinc-500">{count}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[760px]">
          <thead>
            <tr className="border-b border-zinc-800">
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
                <tr key={app.id} className="group border-b border-zinc-800 transition-colors hover:bg-zinc-950/70">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded border border-zinc-800 bg-zinc-900 text-2xs font-semibold text-zinc-300">
                        {app.job.company.slice(0, 2).toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-zinc-200">{app.job.company}</span>
                      {app.is_stale && (
                        <span className="badge border border-amber-500/30 bg-amber-500/10 text-2xs text-amber-300">stale</span>
                      )}
                    </div>
                  </td>
                  <td className="max-w-[180px] truncate px-4 py-3 text-sm text-zinc-300">{app.job.title}</td>
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
                  <td className="py-3 px-4">
                    <button className="text-zinc-500 opacity-0 transition-opacity hover:text-zinc-300 group-hover:opacity-100">
                      <ChevronRight size={14} />
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
