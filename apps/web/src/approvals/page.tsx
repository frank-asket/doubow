'use client'

import { Component, type ReactNode, useEffect, useMemo, useState } from 'react'
import { Bookmark, CheckCircle2, CircleHelp, Link2, List, Loader2, Shield, TrendingUp, X } from 'lucide-react'
import { useSearchParams } from 'next/navigation'
import { approvalsApi } from '../../lib/api'
import { dashboardUi } from '../../lib/dashboardUi'
import { useApprovalStore } from './approvalStore'
import { useApprovals } from './useApprovals'

type DraftVariant = 'base-1' | 'base-2' | 'whatif-1' | 'whatif-2' | 'whatif-3' | 'whatif-4'

type PersistedDraftState = {
  body: string
  baseSalary: number
  equityUnits: number
  signOnBonus: number
  variant: DraftVariant
}

type ActionToast = {
  kind: 'success' | 'error'
  message: string
}

function isDraftVariant(value: string | null): value is DraftVariant {
  return value === 'base-1'
    || value === 'base-2'
    || value === 'whatif-1'
    || value === 'whatif-2'
    || value === 'whatif-3'
    || value === 'whatif-4'
}

function storageKeyForApproval(approvalId: string) {
  return `approvals:drafts:${approvalId}`
}

function asCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function parseBaseSalary(salaryRange?: string | null) {
  if (!salaryRange) return 185000
  const numbers = Array.from(salaryRange.matchAll(/\d[\d,]*/g)).map((m) => Number(m[0].replaceAll(',', '')))
  return numbers[0] ?? 185000
}

function ApprovalsLoadingShell() {
  return (
    <div className="approvals-surface min-h-screen bg-[#f5faf8] text-[#171d1c] dark:bg-slate-950 dark:text-slate-100">
      <main className="flex min-h-screen flex-col">
        <section className="border-b border-[#d9e1dd] bg-white/75 px-5 py-4 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/65">
          <div className="h-3 w-36 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <div className="mt-3 h-7 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <div className="mt-2 h-4 w-80 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
        </section>
        <section className="mx-auto grid w-full max-w-[1700px] flex-1 grid-cols-1 gap-4 bg-[#f0f5f2] p-4 dark:bg-slate-950 lg:grid-cols-12 lg:gap-4">
          <aside className={`${dashboardUi.utilityCard} border-[#d6e5df] dark:border-slate-700 lg:col-span-3`}>
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={`queue-skeleton-${i}`} className="rounded-xl border border-[#d6e5df] bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
                  <div className="h-4 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                  <div className="mt-2 h-3 w-36 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                </div>
              ))}
            </div>
          </aside>
          <div className="lg:col-span-6">
            <div className={`${dashboardUi.utilityCard} border-[#d6e5df] dark:border-slate-700 min-h-[640px] p-0`}>
              <div className="border-b border-[#d6e5df] p-4 dark:border-slate-700">
                <div className="h-3 w-56 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="mt-2 h-5 w-40 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              </div>
              <div className="p-6 space-y-3">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={`composer-skeleton-${i}`} className="h-4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                ))}
              </div>
            </div>
          </div>
          <div className="space-y-4 lg:col-span-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={`side-skeleton-${i}`} className={`${dashboardUi.utilityCard} border-[#d6e5df] dark:border-slate-700`}>
                <div className="h-4 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="mt-3 space-y-2">
                  <div className="h-3 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                  <div className="h-3 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

type ApprovalsWorkspaceBoundaryProps = {
  children: ReactNode
  onReset?: () => void
}

type ApprovalsWorkspaceBoundaryState = {
  hasError: boolean
}

class ApprovalsWorkspaceBoundary extends Component<
  ApprovalsWorkspaceBoundaryProps,
  ApprovalsWorkspaceBoundaryState
> {
  state: ApprovalsWorkspaceBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ApprovalsWorkspaceBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    console.error('Approvals workspace render failure:', error)
  }

  handleReset = () => {
    this.setState({ hasError: false })
    this.props.onReset?.()
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <section className="mx-auto grid w-full max-w-[1700px] flex-1 place-items-center bg-[#f0f5f2] p-6 dark:bg-slate-950">
        <div className="w-full max-w-xl rounded-2xl border border-[#d6e5df] bg-white p-6 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm font-semibold text-slate-900 dark:text-white">Approvals workspace hit a rendering issue.</p>
          <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">
            Your draft data is safe. Reload this panel to continue.
          </p>
          <div className="mt-4 flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={this.handleReset}
              className={`${dashboardUi.actionButton} border border-[#d6e5df] font-medium text-slate-700 dark:border-slate-700 dark:text-slate-200`}
            >
              Reload panel
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className={`${dashboardUi.actionButton} bg-[#00685f] px-4 font-semibold text-white`}
            >
              Reload page
            </button>
          </div>
        </div>
      </section>
    )
  }
}

export default function ApprovalsPage() {
  const searchParams = useSearchParams()
  const { approvals, loading, removeApproval } = useApprovalStore()
  const { refresh } = useApprovals()

  const pending = useMemo(() => approvals.filter((item) => item.status === 'pending'), [approvals])
  const providerConfirmed = useMemo(
    () => approvals.filter((item) => item.delivery_status === 'provider_confirmed'),
    [approvals],
  )
  const recentDelivery = useMemo(
    () => approvals.filter((item) => item.status !== 'pending').slice(0, 5),
    [approvals],
  )
  const [selectedApprovalId, setSelectedApprovalId] = useState<string | null>(null)
  const current = useMemo(
    () => pending.find((item) => item.id === selectedApprovalId) ?? pending[0] ?? null,
    [pending, selectedApprovalId],
  )
  const [draftBody, setDraftBody] = useState('')
  const [baseSalary, setBaseSalary] = useState(205000)
  const [equityUnits, setEquityUnits] = useState(600)
  const [signOnBonus, setSignOnBonus] = useState(25000)
  const [flowVariant, setFlowVariant] = useState<DraftVariant>('base-1')
  const [submitting, setSubmitting] = useState<'approve' | 'reject' | null>(null)
  const [saveToastOpen, setSaveToastOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [workspaceBoundaryKey, setWorkspaceBoundaryKey] = useState(0)
  const [actionToast, setActionToast] = useState<ActionToast | null>(null)
  const [autosaveState, setAutosaveState] = useState<'idle' | 'saving' | 'saved'>('idle')
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null)

  const originalBase = parseBaseSalary(current?.application?.job?.salary_range)
  const targetBonus = 15
  const originalTotal = originalBase + Math.round(originalBase * targetBonus * 0.01)
  const scenarioTotal = baseSalary + signOnBonus + Math.round(equityUnits * 114.5)
  const scenarioDelta = scenarioTotal - originalTotal
  const urlVariant = searchParams.get('variant')
  const variant: DraftVariant = isDraftVariant(urlVariant) ? urlVariant : flowVariant
  const showWhatIf = variant.startsWith('whatif-')
  const showGuardrailV2 = variant !== 'base-1'
  const showCalculatorInputs = variant === 'whatif-2' || variant === 'whatif-3' || variant === 'whatif-4'
  const showSaveScenarioAction = variant === 'whatif-3' || variant === 'whatif-4'
  const showSavedToast = variant === 'whatif-4' || saveToastOpen
  const approvalIdFromUrl = searchParams.get('approvalId')
  const draftWordCount = useMemo(
    () => draftBody.trim().split(/\s+/).filter(Boolean).length,
    [draftBody],
  )
  const draftGuidance = draftWordCount < 80
    ? 'Add more specifics (role fit, outcomes, and next step) to strengthen this message.'
    : draftWordCount > 220
      ? 'Consider tightening to keep it skimmable for recruiters.'
      : 'Length looks healthy for a concise recruiter-ready note.'
  const savedAtLabel = useMemo(() => {
    if (!lastSavedAt) return null
    return new Date(lastSavedAt).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  }, [lastSavedAt])
  const hasDraftChanges = useMemo(() => {
    if (!current) return false
    return (
      draftBody !== current.draft_body
      || baseSalary !== 205000
      || equityUnits !== 600
      || signOnBonus !== 25000
      || variant !== 'base-1'
    )
  }, [current, draftBody, baseSalary, equityUnits, signOnBonus, variant])

  function persistDraftState() {
    if (!current || typeof window === 'undefined') return
    const key = storageKeyForApproval(current.id)
    const payload: PersistedDraftState = {
      body: draftBody,
      baseSalary,
      equityUnits,
      signOnBonus,
      variant,
    }
    window.localStorage.setItem(key, JSON.stringify(payload))
  }

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!approvalIdFromUrl) return
    if (!pending.some((item) => item.id === approvalIdFromUrl)) return
    setSelectedApprovalId(approvalIdFromUrl)
  }, [approvalIdFromUrl, pending])

  useEffect(() => {
    if (pending.length === 0) {
      setSelectedApprovalId(null)
      return
    }
    if (selectedApprovalId && pending.some((item) => item.id === selectedApprovalId)) return
    setSelectedApprovalId(pending[0].id)
  }, [pending, selectedApprovalId])

  useEffect(() => {
    if (!selectedApprovalId) return
    if (typeof document === 'undefined') return
    const row = document.querySelector<HTMLElement>(`[data-approval-id="${selectedApprovalId}"]`)
    if (!row) return
    row.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [selectedApprovalId, pending.length])

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (pending.length === 0) return

    const handler = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return
      const target = event.target as HTMLElement | null
      if (target) {
        const tag = target.tagName
        if (
          target.isContentEditable
          || tag === 'INPUT'
          || tag === 'TEXTAREA'
          || tag === 'SELECT'
        ) {
          return
        }
      }

      const key = event.key
      const isNext = key === 'j' || key === 'ArrowDown'
      const isPrev = key === 'k' || key === 'ArrowUp'
      if (!isNext && !isPrev) return
      event.preventDefault()
      const currentIndex = pending.findIndex((item) => item.id === selectedApprovalId)
      if (isNext) {
        const nextIndex = currentIndex < 0 ? 0 : Math.min(pending.length - 1, currentIndex + 1)
        setSelectedApprovalId(pending[nextIndex]?.id ?? null)
      } else if (isPrev) {
        const prevIndex = currentIndex <= 0 ? 0 : currentIndex - 1
        setSelectedApprovalId(pending[prevIndex]?.id ?? null)
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [pending, selectedApprovalId])

  useEffect(() => {
    if (!current) {
      setDraftBody('')
      setFlowVariant('base-1')
      return
    }
    const key = storageKeyForApproval(current.id)
    const fromStorage = typeof window !== 'undefined' ? window.localStorage.getItem(key) : null
    if (fromStorage) {
      try {
        const parsed = JSON.parse(fromStorage) as Partial<PersistedDraftState>
        setDraftBody(typeof parsed.body === 'string' ? parsed.body : current.draft_body)
        setBaseSalary(typeof parsed.baseSalary === 'number' ? parsed.baseSalary : 205000)
        setEquityUnits(typeof parsed.equityUnits === 'number' ? parsed.equityUnits : 600)
        setSignOnBonus(typeof parsed.signOnBonus === 'number' ? parsed.signOnBonus : 25000)
        setFlowVariant(
          parsed.variant != null && isDraftVariant(parsed.variant) ? parsed.variant : 'base-1',
        )
        return
      } catch {
        // Fall through to defaults if stored payload is invalid.
      }
    }
    setDraftBody(current.draft_body)
    setBaseSalary(205000)
    setEquityUnits(600)
    setSignOnBonus(25000)
    setFlowVariant('base-1')
  }, [current?.id])

  useEffect(() => {
    if (!saveToastOpen) return
    if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-4')
    const timer = window.setTimeout(() => setSaveToastOpen(false), 2200)
    return () => window.clearTimeout(timer)
  }, [saveToastOpen, urlVariant])

  useEffect(() => {
    if (saveToastOpen || isDraftVariant(urlVariant)) return
    if (flowVariant === 'whatif-4') setFlowVariant('whatif-3')
  }, [saveToastOpen, flowVariant, urlVariant])

  useEffect(() => {
    if (!current || !hasDraftChanges) {
      setAutosaveState('idle')
      return
    }
    setAutosaveState('saving')
    const timer = window.setTimeout(() => {
      persistDraftState()
      setAutosaveState('saved')
      setLastSavedAt(Date.now())
    }, 500)
    return () => window.clearTimeout(timer)
  }, [current?.id, draftBody, baseSalary, equityUnits, signOnBonus, variant, hasDraftChanges])

  useEffect(() => {
    if (autosaveState !== 'saved') return
    const timer = window.setTimeout(() => setAutosaveState('idle'), 2200)
    return () => window.clearTimeout(timer)
  }, [autosaveState])

  useEffect(() => {
    if (!actionToast) return
    const timer = window.setTimeout(() => setActionToast(null), 2600)
    return () => window.clearTimeout(timer)
  }, [actionToast])

  async function submitApproval() {
    if (!current) return
    setSubmitting('approve')
    try {
      await approvalsApi.approve(current.id, draftBody)
      if (typeof window !== 'undefined') window.localStorage.removeItem(storageKeyForApproval(current.id))
      await refresh()
      setActionToast({ kind: 'success', message: 'Draft approved and saved to Gmail.' })
    } catch {
      setActionToast({ kind: 'error', message: 'Could not send via Gmail. Please try again.' })
    } finally {
      setSubmitting(null)
    }
  }

  async function rejectApproval() {
    if (!current) return
    setSubmitting('reject')
    try {
      await approvalsApi.reject(current.id)
      if (typeof window !== 'undefined') window.localStorage.removeItem(storageKeyForApproval(current.id))
      removeApproval(current.id)
      setActionToast({ kind: 'success', message: 'Draft rejected successfully.' })
    } catch {
      setActionToast({ kind: 'error', message: 'Could not reject this draft right now.' })
    } finally {
      setSubmitting(null)
    }
  }

  if (!mounted) {
    return <ApprovalsLoadingShell />
  }

  if (loading && pending.length === 0) {
    return <ApprovalsLoadingShell />
  }

  return (
    <div className="approvals-surface min-h-screen bg-[#f5faf8] text-[#171d1c] dark:bg-slate-950 dark:text-slate-100">
      {showSavedToast ? (
        <div className="fixed left-1/2 top-[17px] z-[120] flex -translate-x-1/2 items-center gap-2 rounded-md border border-white/20 bg-[#0d9488] px-4 py-3 text-sm font-medium leading-none text-white shadow-md">
          <CheckCircle2 size={17} />
          Scenario saved successfully
          <button type="button" onClick={() => setSaveToastOpen(false)} className="ml-1 inline-flex items-center opacity-80 hover:opacity-100">
            <X size={14} />
          </button>
        </div>
      ) : null}
      {actionToast ? (
        <div
          className={`fixed left-1/2 top-[64px] z-[119] flex -translate-x-1/2 items-center gap-2 rounded-md border px-4 py-2 text-xs font-semibold leading-none shadow-md ${
            actionToast.kind === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
              : 'border-rose-200 bg-rose-50 text-rose-900'
          }`}
        >
          {actionToast.message}
        </div>
      ) : null}

      <main className="flex min-h-screen flex-col">
        <section className="border-b border-[#d6e5df] bg-white/75 px-6 py-5 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/65">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#00685f] dark:text-teal-300">Approvals Workspace</p>
          <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Draft Approvals</h1>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                Review, refine, and approve outbound drafts before they are sent.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
              <div className="rounded-[2px] border border-[#d9e1dd] bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                <p className="text-slate-500 dark:text-slate-400">Pending</p>
                <p className="mt-0.5 text-lg font-bold text-slate-900 dark:text-white">{pending.length}</p>
              </div>
              <div className="rounded-[2px] border border-[#d9e1dd] bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                <p className="text-slate-500 dark:text-slate-400">Sent (provider-confirmed)</p>
                <p className="mt-0.5 text-lg font-bold text-slate-900 dark:text-white">{providerConfirmed.length}</p>
              </div>
              <div className="rounded-[2px] border border-[#d9e1dd] bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                <p className="text-slate-500 dark:text-slate-400">Channel</p>
                <p className="mt-0.5 font-bold text-slate-900 dark:text-white">{current?.channel ?? '—'}</p>
              </div>
              <div className="rounded-[2px] border border-[#d9e1dd] bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                <p className="text-slate-500 dark:text-slate-400">Variant</p>
                <p className="mt-0.5 font-bold text-slate-900 dark:text-white">{variant}</p>
              </div>
            </div>
          </div>
          <p className="mt-2 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            {autosaveState === 'saving'
              ? 'Saving changes...'
              : autosaveState === 'saved' && savedAtLabel
                ? `Saved at ${savedAtLabel}`
                : hasDraftChanges
                  ? 'Unsaved changes'
                  : savedAtLabel
                    ? `Saved at ${savedAtLabel}`
                    : 'All changes saved'}
          </p>
        </section>

        {!current ? (
          <section className="grid flex-1 place-items-center p-8">
            <div className="w-full max-w-2xl rounded-2xl border border-[#d6e5df] bg-white px-8 py-10 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">No pending drafts</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">New outbound draft requests will appear here.</p>
              {recentDelivery.length > 0 ? (
                <div className="mt-6 space-y-2 text-left">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">
                    Recent delivery status
                  </p>
                  {recentDelivery.map((item) => (
                    <div
                      key={`empty-delivery-${item.id}`}
                      className="flex items-center justify-between rounded-lg border border-[#d6e5df] px-3 py-2 text-xs dark:border-slate-700"
                    >
                      <span className="font-medium text-slate-700 dark:text-slate-200">
                        {item.application.job.company}
                      </span>
                      <span className={item.delivery_status === 'provider_confirmed'
                        ? 'font-semibold text-emerald-700 dark:text-emerald-300'
                        : item.delivery_status === 'failed'
                          ? 'font-semibold text-rose-700 dark:text-rose-300'
                          : 'font-semibold text-slate-600 dark:text-slate-300'}
                      >
                        {item.delivery_status === 'provider_confirmed'
                          ? 'Sent (provider-confirmed)'
                          : item.delivery_status === 'provider_accepted'
                            ? 'Sent (provider-accepted)'
                            : item.delivery_status === 'draft_created'
                              ? 'Draft created (not sent)'
                              : item.delivery_status === 'failed'
                                ? 'Send failed'
                                : item.delivery_status ?? 'Queued'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </section>
        ) : (
          <ApprovalsWorkspaceBoundary
            key={workspaceBoundaryKey}
            onReset={() => setWorkspaceBoundaryKey((v) => v + 1)}
          >
          <section className="mx-auto w-full max-w-[1700px] flex-1 overflow-x-auto bg-[#f0f5f2] p-4 dark:bg-slate-950">
            <div className="grid min-w-[1240px] grid-cols-1 gap-3 lg:grid-cols-[220px_minmax(760px,1fr)_300px] lg:gap-3">
            <aside className={`${dashboardUi.utilityCard} min-w-0 !rounded-[2px] border-[#d9e1dd] p-3 dark:border-slate-700 lg:sticky lg:top-20 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto`}>
              <div className="flex items-center justify-between px-2 pb-2">
                <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Queue</h2>
                <span className="rounded-full border border-[#d6e5df] bg-white px-2 py-0.5 text-[10px] font-semibold tracking-wide text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                  J/K or ↑/↓
                </span>
              </div>
              <div className="space-y-2">
                {pending.map((item) => {
                  const selected = current?.id === item.id
                  return (
                    <button
                      key={item.id}
                      data-approval-id={item.id}
                      type="button"
                      onClick={() => setSelectedApprovalId(item.id)}
                      className={`w-full rounded-[2px] border px-3 py-2.5 text-left transition-all ${
                        selected
                          ? 'border-[#0d9488] bg-[#ecfdfb] shadow-sm dark:border-teal-500/60 dark:bg-teal-500/10'
                          : 'border-[#d9e1dd] bg-white hover:-translate-y-[1px] hover:shadow-sm dark:border-slate-700 dark:bg-slate-900'
                      }`}
                    >
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.application.job.company}</p>
                      <p className="mt-1 line-clamp-1 text-xs text-slate-600 dark:text-slate-300">{item.application.job.title}</p>
                      <div className="mt-2 flex items-center justify-between text-[11px]">
                        <span className="rounded-full border border-slate-200 px-2 py-0.5 uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-300">
                          {item.channel}
                        </span>
                        <span className="font-medium text-[#00685f] dark:text-teal-300">Pending</span>
                      </div>
                    </button>
                  )
                })}
              </div>
              <div className="mt-3 border-t border-[#d9e1dd] pt-3 dark:border-slate-700">
                <h3 className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">
                  Recent delivery
                </h3>
                <div className="space-y-2">
                  {recentDelivery.length === 0 ? (
                    <p className="px-2 text-xs text-slate-500 dark:text-slate-400">
                      No sent confirmations yet.
                    </p>
                  ) : (
                    recentDelivery.map((item) => (
                      <div
                        key={`delivery-${item.id}`}
                        className="rounded-[2px] border border-[#d9e1dd] bg-white px-3 py-2.5 dark:border-slate-700 dark:bg-slate-900"
                      >
                        <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.application.job.company}</p>
                        <p className="mt-1 line-clamp-1 text-xs text-slate-600 dark:text-slate-300">{item.application.job.title}</p>
                        <div className="mt-2 flex items-center justify-between text-[11px]">
                          <span className="rounded-full border border-slate-200 px-2 py-0.5 uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-300">
                            {item.send_provider ?? item.channel}
                          </span>
                          <span className={item.delivery_status === 'provider_confirmed'
                            ? 'font-medium text-emerald-700 dark:text-emerald-300'
                            : item.delivery_status === 'failed'
                              ? 'font-medium text-rose-700 dark:text-rose-300'
                              : item.delivery_status === 'draft_created'
                                ? 'font-medium text-amber-700 dark:text-amber-300'
                                : 'font-medium text-slate-600 dark:text-slate-300'}
                          >
                            {item.delivery_status === 'provider_confirmed'
                              ? 'Sent (provider-confirmed)'
                              : item.delivery_status === 'provider_accepted'
                                ? 'Sent (provider-accepted)'
                                : item.delivery_status === 'draft_created'
                                  ? 'Draft created (not sent)'
                                  : item.delivery_status === 'failed'
                                    ? 'Send failed'
                                    : item.delivery_status ?? 'Queued'}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </aside>

            <div className="min-w-0">
              <div className={`${dashboardUi.utilityCard} min-w-0 !rounded-[2px] border-[#d9e1dd] dark:border-slate-700 flex min-h-[700px] flex-col p-0`}>
                <div className="flex h-10 flex-wrap items-center justify-between gap-2 border-b border-[#d9e1dd] bg-slate-50/70 px-3 py-2 dark:border-slate-700 dark:bg-slate-900/50">
                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">
                      {current.application.job.company} · {current.application.job.title}
                    </p>
                    <p className="text-sm font-bold text-slate-900 dark:text-white">Draft Composer</p>
                  </div>
                  <div className="flex items-center gap-0.5 text-slate-600 dark:text-slate-300">
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><strong className="text-xs">B</strong></button>
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><em className="text-xs">I</em></button>
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><List size={13} /></button>
                    <div className="mx-1 h-4 w-px bg-slate-200" />
                    <button type="button" className="rounded p-1.5 hover:bg-slate-100"><Link2 size={13} /></button>
                  </div>
                  <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setDraftBody(current.draft_body)}
                    className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#d9e1dd] bg-white px-2.5 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                  >
                    <CircleHelp size={12} />
                    Revert to Original
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setDraftBody((prev) => `${prev}\n\nI can also share specific Cloud Infrastructure outcomes to support this request.`)
                      if (!isDraftVariant(urlVariant)) {
                        setFlowVariant((prev) => (prev === 'base-1' ? 'base-2' : prev))
                      }
                    }}
                    className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#44cfc0] bg-[#6bd8cb] px-2.5 text-[11px] font-semibold text-[#005049]"
                  >
                    <CheckCircle2 size={12} />
                    AI Refine
                  </button>
                </div>
                </div>
                <textarea
                  value={draftBody}
                  onChange={(event) => setDraftBody(event.target.value)}
                  aria-label="Draft editor"
                  className={`${dashboardUi.composerSurface} min-h-[720px] bg-white p-6 text-[14px] leading-[1.55]`}
                />
                <div className="sticky bottom-0 z-10 flex h-11 items-center justify-between border-t border-[#d9e1dd] bg-white px-3 dark:border-slate-700 dark:bg-slate-900">
                  <button type="button" onClick={() => current && setDraftBody(current.draft_body)} className="inline-flex h-7 items-center rounded-[2px] border border-[#d9e1dd] bg-white px-2.5 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                    Cancel
                  </button>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-1')
                        persistDraftState()
                        setAutosaveState('saved')
                        setLastSavedAt(Date.now())
                        setActionToast({ kind: 'success', message: 'Draft progress saved.' })
                      }}
                      className="inline-flex h-7 items-center rounded-[2px] border border-[#d9e1dd] bg-white px-2.5 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                    >
                      Save as Draft
                    </button>
                    <button type="button" onClick={() => void submitApproval()} disabled={!current || submitting !== null} className="inline-flex h-7 items-center gap-1 rounded-[2px] bg-[#00685f] px-3 text-[11px] font-semibold text-white disabled:opacity-60">
                      {submitting === 'approve' ? <Loader2 size={12} className="animate-spin" /> : null}
                      Send via Gmail
                    </button>
                    <button type="button" onClick={() => void rejectApproval()} disabled={!current || submitting !== null} className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#d9e1dd] bg-white px-2.5 text-[11px] font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 disabled:opacity-60">
                      {submitting === 'reject' ? <Loader2 size={12} className="animate-spin" /> : <X size={12} />}
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="min-w-0 space-y-3 lg:sticky lg:top-20 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto">
              <div className={`${dashboardUi.utilityCard} !rounded-[2px] border-[#d9e1dd] p-3 dark:border-slate-700`}>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Offer Snapshot</h3>
                <div className="space-y-2 text-[13px]">
                  <div className="flex items-center justify-between border-b border-[#e2e8f0] pb-2 dark:border-slate-700"><span className="text-slate-500 dark:text-slate-400">Base Salary</span><span className="font-semibold">{asCurrency(originalBase)}</span></div>
                  <div className="flex items-center justify-between border-b border-[#e2e8f0] pb-2 dark:border-slate-700"><span className="text-slate-500 dark:text-slate-400">Equity (GSUs)</span><span className="font-semibold">450 Units</span></div>
                  <div className="flex items-center justify-between border-b border-[#e2e8f0] pb-2 dark:border-slate-700"><span className="text-slate-500 dark:text-slate-400">Target Bonus</span><span className="font-semibold">15%</span></div>
                  <div className="flex items-center justify-between pt-1"><span className="font-medium text-slate-800 dark:text-slate-200">Total Comp (Est)</span><span className="font-bold text-[#00685f]">{asCurrency(originalTotal)}</span></div>
                </div>
              </div>

              {showWhatIf ? (
                <div className={`${dashboardUi.utilityCard} !rounded-[2px] border-[#d9e1dd] p-3 dark:border-slate-700`}>
                  <h3 className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">What-If Calculator</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="mb-1 flex justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Base Salary</label>
                        {showCalculatorInputs ? (
                          <div className="flex items-center gap-1 rounded border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 px-2 py-1">
                            <span className="text-[11px] font-medium text-slate-400">$</span>
                            <input
                              value={baseSalary.toLocaleString('en-US')}
                              onChange={(e) => setBaseSalary(Number(e.target.value.replaceAll(',', '')) || 0)}
                              className="w-16 border-none bg-transparent p-0 text-right text-xs font-semibold text-slate-700 focus:outline-none"
                            />
                          </div>
                        ) : (
                        <span className="text-xs font-semibold leading-none text-slate-700">{asCurrency(baseSalary)}</span>
                        )}
                      </div>
                      <input
                        type="range"
                        min={150000}
                        max={300000}
                        step={1000}
                        value={baseSalary}
                        onChange={(e) => {
                          setBaseSalary(Number(e.target.value))
                          if (!isDraftVariant(urlVariant)) setFlowVariant((prev) => (prev === 'whatif-1' ? 'whatif-2' : prev))
                        }}
                        className="h-1 w-full cursor-pointer rounded-lg bg-slate-100 accent-[#00685f]"
                      />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Equity (GSUs)</label>
                        {showCalculatorInputs ? (
                          <div className="flex items-center gap-1 rounded border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 px-2 py-1">
                            <input
                              value={equityUnits}
                              onChange={(e) => setEquityUnits(Number(e.target.value) || 0)}
                              className="w-8 border-none bg-transparent p-0 text-right text-xs font-semibold text-slate-700 focus:outline-none"
                            />
                            <span className="text-[11px] font-medium text-slate-400">Units</span>
                          </div>
                        ) : (
                        <span className="text-xs font-semibold leading-none text-slate-700">{equityUnits} Units</span>
                        )}
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={1000}
                        step={10}
                        value={equityUnits}
                        onChange={(e) => {
                          setEquityUnits(Number(e.target.value))
                          if (!isDraftVariant(urlVariant)) setFlowVariant((prev) => (prev === 'whatif-1' ? 'whatif-2' : prev))
                        }}
                        className="h-1 w-full cursor-pointer rounded-lg bg-slate-100 accent-[#00685f]"
                      />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Sign-on Bonus</label>
                        {showCalculatorInputs ? (
                          <div className="flex items-center gap-1 rounded border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 px-2 py-1">
                            <span className="text-[11px] font-medium text-slate-400">$</span>
                            <input
                              value={signOnBonus.toLocaleString('en-US')}
                              onChange={(e) => setSignOnBonus(Number(e.target.value.replaceAll(',', '')) || 0)}
                              className="w-14 border-none bg-transparent p-0 text-right text-xs font-semibold text-slate-700 focus:outline-none"
                            />
                          </div>
                        ) : (
                        <span className="text-xs font-semibold leading-none text-slate-700">{asCurrency(signOnBonus)}</span>
                        )}
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={100000}
                        step={5000}
                        value={signOnBonus}
                        onChange={(e) => {
                          setSignOnBonus(Number(e.target.value))
                          if (!isDraftVariant(urlVariant)) setFlowVariant((prev) => (prev === 'whatif-1' ? 'whatif-2' : prev))
                        }}
                        className="h-1 w-full cursor-pointer rounded-lg bg-slate-100 accent-[#00685f]"
                      />
                    </div>
                    <div className={`${showCalculatorInputs ? 'pt-4' : 'pt-3'} border-t border-[#e2e8f0] dark:border-slate-700`}>
                      <div className={`${showCalculatorInputs ? 'mb-1.5' : 'mb-1'} flex items-center justify-between`}>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Scenario Total</span>
                        <div className="flex items-center gap-3">
                          {showSaveScenarioAction ? (
                            <button
                              type="button"
                              onClick={() => {
                                if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-3')
                                setSaveToastOpen(true)
                              }}
                              className={`${dashboardUi.actionButton} gap-1 border border-[#e2e8f0] dark:border-slate-700 px-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#00685f]`}
                            >
                              <Bookmark size={dashboardUi.actionIcon} />
                              Save Scenario
                            </button>
                          ) : null}
                          <span className={`font-bold text-slate-900 dark:text-slate-100 ${showSaveScenarioAction ? 'text-lg' : 'text-[14px]'}`}>{asCurrency(scenarioTotal)}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Delta from Original</span>
                        <span className="inline-flex items-center gap-1 text-xs font-bold leading-none text-[#00685f]">
                          <TrendingUp size={dashboardUi.actionIcon} />
                          +{asCurrency(scenarioDelta)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}

              <div className={`${dashboardUi.utilityCard} !rounded-[2px] border-[#d9e1dd] p-3 dark:border-slate-700 border-l-2 border-l-amber-600`}>
                <h3 className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-amber-700">AI Feedback</h3>
                <p className="text-[13px] text-slate-600 dark:text-slate-300">Tone is professional, appreciative, and data-driven.</p>
                <p className="mt-2 text-[13px] text-slate-600 dark:text-slate-300">Suggestion: Highlight specific Cloud Infrastructure metrics to justify the increase.</p>
              </div>

              <div className={`${dashboardUi.utilityCard} !rounded-[2px] border-[#d9e1dd] p-3 dark:border-slate-700 border-l-2 border-l-[#0d9488]`}>
                <h3 className="mb-2 inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-[#00685f]">
                  <Shield size={dashboardUi.actionIcon} />
                  Negotiation Guardrails
                </h3>
                {showGuardrailV2 ? (
                  <div>
                    <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Market Benchmark (L5 Software Engineer)</p>
                    <div className="relative mb-6 h-12">
                      <div className="absolute bottom-4 left-0 right-0 h-px bg-slate-200" />
                      <div className="absolute bottom-3 left-0 flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P25<span className="text-[10px] text-slate-500 dark:text-slate-400">$180k</span></div>
                      <div className="absolute bottom-3 left-[33%] flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P50<span className="text-[10px] text-slate-500 dark:text-slate-400">$205k</span></div>
                      <div className="absolute bottom-3 left-[66%] flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P75<span className="text-[10px] text-slate-500 dark:text-slate-400">$225k</span></div>
                      <div className="absolute bottom-3 right-0 flex flex-col items-center text-[9px] font-medium text-slate-400"><div className="mb-1 h-2 w-px bg-slate-300" />P90<span className="text-[10px] text-slate-500 dark:text-slate-400">$245k</span></div>
                      <div className="absolute bottom-4 left-[10%] right-[30%] h-1 rounded-full bg-[#0d9488]/20" />
                      <div className="absolute bottom-1 left-[15%] flex flex-col items-center">
                        <div className="mb-1 h-2 w-2 rounded-full border-2 border-white bg-slate-400 shadow-sm" />
                        <span className="whitespace-nowrap text-[9px] font-bold uppercase tracking-tight leading-none text-slate-400">Current Offer</span>
                      </div>
                      <div className="absolute bottom-1 left-[45%] flex flex-col items-center">
                        <div className="mb-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-[#0d9488] shadow-sm" />
                        <span className="whitespace-nowrap text-[9px] font-bold uppercase tracking-tight leading-none text-[#0d9488]">Target Range</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">Market Benchmark (L5)</p>
                    <div className="relative h-1.5 rounded-full bg-slate-100">
                      <div className="absolute left-[30%] right-[20%] top-0 h-1.5 rounded-full bg-[#89f5e7]" />
                      <div className="absolute left-[55%] top-0 h-1.5 w-[2px] bg-[#00685f]" />
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[9px] uppercase text-slate-400">
                      <span>$175k</span>
                      <span className="font-bold text-[#00685f]">Current Target</span>
                      <span>$230k</span>
                    </div>
                  </div>
                )}
                <div className="mt-3 border border-[#e2e8f0] dark:border-slate-700 bg-slate-50 dark:bg-slate-900/80 p-2">
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">Recruiter Notes</p>
                  <p className="text-[11px] italic leading-[1.3] text-slate-600 dark:text-slate-300">
                    Sarah is data-centric. Responds best to external offer comparisons or internal equity parity arguments.
                  </p>
                </div>
              </div>
            </div>
            </div>
          </section>
          </ApprovalsWorkspaceBoundary>
        )}
      </main>
    </div>
  )
}
