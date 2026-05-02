'use client'

import { Component, type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Bookmark, CheckCircle2, CircleHelp, Link2, List, Loader2, Mail, Shield, TrendingUp, X } from 'lucide-react'
import { useSearchParams } from 'next/navigation'
import type { Approval } from '@doubow/shared'
import { ApiError, approvalsApi, googleIntegrationsApi, linkedinIntegrationsApi } from '../../lib/api'
import { dashboardUi } from '../../lib/dashboardUi'
import { motion, useReducedMotion, fadeInUpVariants, staggerContainerVariants, getMicroInteractionMotion } from '../../lib/motion'
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

function isRenderableApproval(value: unknown): value is Approval {
  if (!value || typeof value !== 'object') return false
  const item = value as Partial<Approval> & { application?: { job?: { company?: string; title?: string } } }
  return Boolean(
    item.id
    && item.status
    && item.channel
    && item.application?.job?.company
    && item.application?.job?.title,
  )
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

function handoffSuccessToastMessage(channel: string, row?: Approval | null) {
  if (!row) {
    return channel === 'linkedin'
      ? 'Approved. We are emailing you the LinkedIn message — check your inbox in a moment.'
      : 'Approved. Your message is on its way — see status under Recent delivery below.'
  }
  if (row.delivery_status === 'failed') {
    const hint = row.delivery_error ? ` (${row.delivery_error})` : ''
    return `Could not send${hint}. Try again, or open Settings to reconnect Gmail or LinkedIn.`
  }
  if (row.channel === 'linkedin' && row.send_provider === 'linkedin_email_handoff') {
    return 'We emailed you the text to use on LinkedIn — open the job, then paste from your inbox.'
  }
  if (row.delivery_status === 'draft_created') {
    return 'A draft was saved in Gmail. Open Gmail to review and send when you are ready.'
  }
  if (row.delivery_status === 'provider_confirmed' && row.send_provider === 'gmail') {
    return 'Sent from your Gmail account.'
  }
  if (row.send_provider === 'smtp') {
    return 'Sent through Doubow’s email service.'
  }
  return 'Draft approved.'
}

function approvalDeliveryBadgeClass(item: Approval) {
  if (item.send_provider === 'linkedin_email_handoff' || item.delivery_status === 'provider_confirmed') {
    return 'font-semibold text-emerald-700 dark:text-emerald-300'
  }
  if (item.delivery_status === 'failed') return 'font-semibold text-rose-700 dark:text-rose-300'
  if (item.delivery_status === 'draft_created') return 'font-semibold text-amber-700 dark:text-amber-300'
  return 'font-semibold text-slate-600 dark:text-slate-300'
}

function approvalDeliverySummary(item: Approval) {
  if (item.send_provider === 'linkedin_email_handoff') return 'Emailed for LinkedIn (paste on site)'
  if (item.delivery_status === 'provider_confirmed') return 'Sent (confirmed)'
  if (item.delivery_status === 'provider_accepted') return 'Sent (accepted)'
  if (item.delivery_status === 'draft_created') return 'Saved as Gmail draft'
  if (item.delivery_status === 'failed') return 'Not sent'
  return item.delivery_status ?? 'In progress'
}

function confirmationCopySummary(item: Approval) {
  const status = item.confirmation_copy_status ?? 'pending'
  if (status === 'delivered') return 'Copy to you: delivered'
  if (status === 'failed') return 'Copy to you: failed'
  if (status === 'not_applicable') return 'No extra copy'
  return 'Copy to you: pending'
}

function confirmationCopyBadgeClass(item: Approval) {
  const status = item.confirmation_copy_status ?? 'pending'
  if (status === 'delivered') return 'font-semibold text-emerald-700 dark:text-emerald-300'
  if (status === 'failed') return 'font-semibold text-rose-700 dark:text-rose-300'
  if (status === 'not_applicable') return 'font-semibold text-slate-500 dark:text-slate-400'
  return 'font-semibold text-amber-700 dark:text-amber-300'
}

/** Readable channel label for how the message was sent (avoid raw provider ids). */
function sendChannelLabel(item: Pick<Approval, 'channel' | 'send_provider'>): string {
  const sp = item.send_provider
  if (sp === 'linkedin_email_handoff') return 'LinkedIn'
  if (sp === 'gmail') return 'Gmail'
  if (sp === 'smtp') return 'Email'
  if (item.channel === 'linkedin') return 'LinkedIn'
  if (item.channel === 'email') return 'Email'
  return sp ?? item.channel
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
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#00685f] dark:text-teal-300">Approvals Workspace</p>
          <h1 className="mt-2 text-xl font-bold tracking-tight text-slate-900 dark:text-white">Draft Approvals</h1>
          <div className="mt-2 h-4 w-80 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
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
  const { refresh, error } = useApprovals()
  const renderableApprovals = useMemo(() => approvals.filter(isRenderableApproval), [approvals])
  const malformedApprovalsCount = approvals.length - renderableApprovals.length

  const pending = useMemo(() => renderableApprovals.filter((item) => item.status === 'pending'), [renderableApprovals])
  const providerConfirmed = useMemo(
    () => renderableApprovals.filter((item) => item.delivery_status === 'provider_confirmed'),
    [renderableApprovals],
  )
  const recentDelivery = useMemo(
    () => renderableApprovals.filter((item) => item.status !== 'pending').slice(0, 5),
    [renderableApprovals],
  )
  const [showConfirmationFailuresOnly, setShowConfirmationFailuresOnly] = useState(false)
  const filteredRecentDelivery = useMemo(() => {
    if (!showConfirmationFailuresOnly) return recentDelivery
    return recentDelivery.filter((item) => item.confirmation_copy_status === 'failed')
  }, [recentDelivery, showConfirmationFailuresOnly])
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
  const [gmailForApprovals, setGmailForApprovals] = useState<{
    loading: boolean
    connected: boolean
    google_email: string | null
    error: string | null
  } | null>(null)
  const [linkedinForApprovals, setLinkedinForApprovals] = useState<{
    loading: boolean
    connected: boolean
    error: string | null
  } | null>(null)

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

  const approveButtonLabel = useMemo(() => {
    if (!current) return 'Approve'
    if (current.channel === 'linkedin') return 'Approve & email me for LinkedIn'
    if (current.channel === 'email') {
      if (gmailForApprovals?.loading) return 'Approve & send…'
      if (gmailForApprovals?.connected) return 'Approve & send via Gmail'
      return 'Approve & send through Doubow'
    }
    return 'Approve'
  }, [current, gmailForApprovals])
  const prefersReducedMotion = useReducedMotion()
  const motionEnabled = !prefersReducedMotion
  const microInteractionMotion = getMicroInteractionMotion(motionEnabled)

  useEffect(() => {
    if (!current) {
      setGmailForApprovals(null)
      setLinkedinForApprovals(null)
      return
    }
    let cancelled = false
    const run = async () => {
      if (current.channel === 'email') {
        setGmailForApprovals({ loading: true, connected: false, google_email: null, error: null })
        setLinkedinForApprovals(null)
        try {
          const s = await googleIntegrationsApi.status()
          if (!cancelled) {
            setGmailForApprovals({
              loading: false,
              connected: s.connected,
              google_email: s.google_email,
              error: null,
            })
          }
        } catch (e) {
          if (!cancelled) {
            setGmailForApprovals({
              loading: false,
              connected: false,
              google_email: null,
              error: e instanceof ApiError ? e.detail : 'Could not load Gmail status.',
            })
          }
        }
        return
      }
      if (current.channel === 'linkedin') {
        setLinkedinForApprovals({ loading: true, connected: false, error: null })
        setGmailForApprovals(null)
        try {
          const s = await linkedinIntegrationsApi.status()
          if (!cancelled) {
            setLinkedinForApprovals({ loading: false, connected: s.connected, error: null })
          }
        } catch (e) {
          if (!cancelled) {
            setLinkedinForApprovals({
              loading: false,
              connected: false,
              error: e instanceof ApiError ? e.detail : 'Could not load LinkedIn status.',
            })
          }
        }
        return
      }
      setGmailForApprovals(null)
      setLinkedinForApprovals(null)
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [current])

  const persistDraftState = useCallback(() => {
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
  }, [current, draftBody, baseSalary, equityUnits, signOnBonus, variant])

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
  }, [current])

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
  }, [current, hasDraftChanges, persistDraftState])

  useEffect(() => {
    if (autosaveState !== 'saved') return
    const timer = window.setTimeout(() => setAutosaveState('idle'), 2200)
    return () => window.clearTimeout(timer)
  }, [autosaveState])

  useEffect(() => {
    if (malformedApprovalsCount > 0) {
      console.error('Approvals payload dropped malformed rows', {
        total: approvals.length,
        malformed: malformedApprovalsCount,
      })
    }
  }, [approvals.length, malformedApprovalsCount])

  useEffect(() => {
    if (!error) return
    console.error('Approvals fetch error', error)
  }, [error])

  useEffect(() => {
    if (!actionToast) return
    const timer = window.setTimeout(() => setActionToast(null), 2600)
    return () => window.clearTimeout(timer)
  }, [actionToast])

  async function submitApproval() {
    if (!current) return
    const approvalId = current.id
    const channel = current.channel
    setSubmitting('approve')
    try {
      await approvalsApi.approve(approvalId, draftBody)
      if (typeof window !== 'undefined') window.localStorage.removeItem(storageKeyForApproval(approvalId))
      await refresh()
      await new Promise((r) => setTimeout(r, 150))
      await refresh()
      const updated = useApprovalStore.getState().approvals.find((a) => a.id === approvalId)
      const msg = handoffSuccessToastMessage(channel, updated)
      if (updated?.delivery_status === 'failed') {
        setActionToast({ kind: 'error', message: msg })
      } else {
        setActionToast({ kind: 'success', message: msg })
      }
    } catch {
      setActionToast({
        kind: 'error',
        message: 'Could not complete approval. Check Gmail or LinkedIn in Settings and try again.',
      })
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
    <motion.div
      className="approvals-surface min-h-screen bg-[#f5faf8] text-[#171d1c] dark:bg-slate-950 dark:text-slate-100"
      variants={motionEnabled ? staggerContainerVariants : undefined}
      initial={motionEnabled ? 'hidden' : false}
      animate={motionEnabled ? 'visible' : undefined}
    >
      {showSavedToast ? (
        <div className="fixed left-1/2 top-[17px] z-[120] flex -translate-x-1/2 items-center gap-2 rounded-md border border-white/20 bg-[#0d9488] px-4 py-3 text-sm font-medium leading-none text-white shadow-md">
          <CheckCircle2 size={17} />
          Scenario saved successfully
          <motion.button type="button" onClick={() => setSaveToastOpen(false)} {...microInteractionMotion} className="ml-1 inline-flex items-center opacity-80 hover:opacity-100">
            <X size={14} />
          </motion.button>
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
                <p className="text-slate-500 dark:text-slate-400">Sent (confirmed)</p>
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
          {malformedApprovalsCount > 0 ? (
            <p className="mt-1 text-[11px] font-medium text-amber-700 dark:text-amber-300">
              Some approval entries were skipped because they were incomplete. Check browser console for details.
            </p>
          ) : null}
        </section>

        {current && current.channel === 'email' && gmailForApprovals?.error ? (
          <section className="border-b border-amber-200 bg-amber-50 px-6 py-3 dark:border-amber-900/50 dark:bg-amber-950/40">
            <div className="mx-auto flex max-w-[1700px] flex-wrap items-center justify-between gap-2 text-xs text-amber-950 dark:text-amber-100">
              <span className="flex items-center gap-2 font-medium">
                <Mail size={14} aria-hidden />
                {gmailForApprovals.error}
              </span>
              <button
                type="button"
                onClick={() => {
                  setGmailForApprovals((s) => (s ? { ...s, loading: true, error: null } : s))
                  void googleIntegrationsApi
                    .status()
                    .then((s) => {
                      setGmailForApprovals({
                        loading: false,
                        connected: s.connected,
                        google_email: s.google_email,
                        error: null,
                      })
                    })
                    .catch((e) => {
                      setGmailForApprovals({
                        loading: false,
                        connected: false,
                        google_email: null,
                        error: e instanceof ApiError ? e.detail : 'Could not load Gmail status.',
                      })
                    })
                }}
                className="rounded-[2px] border border-amber-300 bg-white px-2 py-1 text-[11px] font-semibold text-amber-900 hover:bg-amber-100 dark:border-amber-800 dark:bg-slate-900 dark:text-amber-100 dark:hover:bg-slate-800"
              >
                Retry
              </button>
            </div>
          </section>
        ) : null}

        {current && current.channel === 'email' && gmailForApprovals && !gmailForApprovals.loading && !gmailForApprovals.connected && !gmailForApprovals.error ? (
          <section className="border-b border-[#d6e5df] bg-[#ecfdfb] px-6 py-3 dark:border-slate-800 dark:bg-teal-950/30">
            <div className="mx-auto flex max-w-[1700px] flex-wrap items-center justify-between gap-3 text-xs text-slate-800 dark:text-slate-200">
              <p className="min-w-0 flex-1 leading-relaxed">
                <span className="font-semibold text-[#00685f] dark:text-teal-300">Gmail is not connected.</span>{' '}
                We can still send using Doubow’s email service. Connect Google in Settings to save drafts in Gmail or send from your own address when that option is available.
              </p>
              <Link
                href="/settings"
                className="shrink-0 rounded-[2px] border border-[#00685f] bg-[#00685f] px-3 py-1.5 text-[11px] font-semibold text-white hover:opacity-95"
              >
                Open Settings
              </Link>
            </div>
          </section>
        ) : null}

        {current && current.channel === 'linkedin' && linkedinForApprovals?.error ? (
          <section className="border-b border-amber-200 bg-amber-50 px-6 py-3 dark:border-amber-900/50 dark:bg-amber-950/40">
            <div className="mx-auto flex max-w-[1700px] flex-wrap items-center justify-between gap-2 text-xs text-amber-950 dark:text-amber-100">
              <span>{linkedinForApprovals.error}</span>
              <button
                type="button"
                onClick={() => {
                  setLinkedinForApprovals({ loading: true, connected: false, error: null })
                  void linkedinIntegrationsApi
                    .status()
                    .then((s) => {
                      setLinkedinForApprovals({ loading: false, connected: s.connected, error: null })
                    })
                    .catch((e) => {
                      setLinkedinForApprovals({
                        loading: false,
                        connected: false,
                        error: e instanceof ApiError ? e.detail : 'Could not load LinkedIn status.',
                      })
                    })
                }}
                className="rounded-[2px] border border-amber-300 bg-white px-2 py-1 text-[11px] font-semibold text-amber-900 dark:border-amber-800 dark:bg-slate-900 dark:text-amber-100"
              >
                Retry
              </button>
            </div>
          </section>
        ) : null}

        {current && current.channel === 'linkedin' && linkedinForApprovals && !linkedinForApprovals.loading && !linkedinForApprovals.connected && !linkedinForApprovals.error ? (
          <section className="border-b border-[#d6e5df] bg-slate-50 px-6 py-3 dark:border-slate-800 dark:bg-slate-900/50">
            <p className="mx-auto max-w-[1700px] text-xs leading-relaxed text-slate-700 dark:text-slate-300">
              <span className="font-semibold text-slate-900 dark:text-white">LinkedIn is not connected.</span>{' '}
              You can still approve — Doubow emails you the note to paste on the posting. Link LinkedIn in Settings for profile sync.
              {' '}
              <Link href="/settings" className="font-semibold text-[#00685f] underline-offset-2 hover:underline dark:text-teal-300">
                Settings
              </Link>
            </p>
          </section>
        ) : null}

        {!current ? (
          <section className="grid flex-1 place-items-center p-8">
            <div className="w-full max-w-2xl rounded-2xl border border-[#d6e5df] bg-white px-8 py-10 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">No pending drafts</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">New outbound draft requests will appear here.</p>
              {recentDelivery.length > 0 ? (
                <div className="mt-6 space-y-2 text-left">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">
                      Recent delivery status
                    </p>
                    <button
                      type="button"
                      onClick={() => setShowConfirmationFailuresOnly((v) => !v)}
                      className={`rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.08em] ${
                        showConfirmationFailuresOnly
                          ? 'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-200'
                          : 'border-[#d6e5df] bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'
                      }`}
                    >
                      {showConfirmationFailuresOnly ? 'Showing issues only' : 'Show email-copy issues only'}
                    </button>
                  </div>
                  {filteredRecentDelivery.length === 0 ? (
                    <p className="text-xs text-slate-500 dark:text-slate-400">No email-copy issues in recent sends.</p>
                  ) : null}
                  {filteredRecentDelivery.map((item) => (
                    <div key={`empty-delivery-${item.id}`} className="space-y-1">
                      <div className="flex items-center justify-between rounded-lg border border-[#d6e5df] px-3 py-2 text-xs dark:border-slate-700">
                        <span className="font-medium text-slate-700 dark:text-slate-200">
                          {item.application.job.company}
                        </span>
                        <span className={approvalDeliveryBadgeClass(item)}>
                          {approvalDeliverySummary(item)}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className={confirmationCopyBadgeClass(item)}>
                          {confirmationCopySummary(item)}
                        </span>
                      </div>
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
          <section className="mx-auto w-full max-w-[1700px] flex-1 overflow-x-auto bg-[#f0f5f2] p-6 dark:bg-slate-950">
            <div className="grid min-w-[1240px] grid-cols-1 gap-4 lg:grid-cols-[220px_minmax(760px,1fr)_300px] lg:gap-4">
            <aside className={`${dashboardUi.utilityCard} min-w-0 !rounded-[2px] border-[#E2E8F0] p-3 dark:border-slate-700 lg:sticky lg:top-20 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto`}>
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
                    <motion.button
                      key={item.id}
                      data-approval-id={item.id}
                      type="button"
                      onClick={() => setSelectedApprovalId(item.id)}
                      {...microInteractionMotion}
                      className={`w-full rounded-[2px] border px-3 py-2.5 text-left transition-all ${
                        selected
                          ? 'border-[#0d9488] bg-[#ecfdfb] shadow-sm dark:border-teal-500/60 dark:bg-teal-500/10'
                          : 'border-[#E2E8F0] bg-white hover:-translate-y-[1px] hover:shadow-sm dark:border-slate-700 dark:bg-slate-900'
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
                    </motion.button>
                  )
                })}
              </div>
              <div className="mt-3 border-t border-[#E2E8F0] pt-3 dark:border-slate-700">
                <div className="flex items-center justify-between gap-2 px-2 pb-2">
                  <h3 className="text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">
                    Recent delivery
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowConfirmationFailuresOnly((v) => !v)}
                    className={`rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.08em] ${
                      showConfirmationFailuresOnly
                        ? 'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-200'
                        : 'border-[#d6e5df] bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'
                    }`}
                  >
                    Issues only
                  </button>
                </div>
                <div className="space-y-2">
                  {filteredRecentDelivery.length === 0 ? (
                    <p className="px-2 text-xs text-slate-500 dark:text-slate-400">
                      {showConfirmationFailuresOnly
                        ? 'No email-copy issues in recent sends.'
                        : 'No recent sends yet.'}
                    </p>
                  ) : (
                    filteredRecentDelivery.map((item) => (
                      <div
                        key={`delivery-${item.id}`}
                        className="rounded-[2px] border border-[#E2E8F0] bg-white px-3 py-2.5 dark:border-slate-700 dark:bg-slate-900"
                      >
                        <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.application.job.company}</p>
                        <p className="mt-1 line-clamp-1 text-xs text-slate-600 dark:text-slate-300">{item.application.job.title}</p>
                        <div className="mt-2 flex items-center justify-between text-[11px]">
                          <span className="rounded-full border border-slate-200 px-2 py-0.5 uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:text-slate-300">
                            {sendChannelLabel(item)}
                          </span>
                          <span className={approvalDeliveryBadgeClass(item)}>
                            {approvalDeliverySummary(item)}
                          </span>
                        </div>
                        <p className={`mt-1 text-[11px] ${confirmationCopyBadgeClass(item)}`}>
                          {confirmationCopySummary(item)}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </aside>

            <div className="min-w-0">
              <div className={`${dashboardUi.utilityCard} min-w-0 !rounded-[2px] border-[#E2E8F0] dark:border-slate-700 flex min-h-[700px] flex-col p-0`}>
                <div className="flex h-11 flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] bg-slate-50/50 px-2 py-2 dark:border-slate-700 dark:bg-slate-900/50">
                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold uppercase tracking-[0.1em] text-slate-500 dark:text-slate-400">
                      {current.application.job.company} · {current.application.job.title}
                    </p>
                    <p className="text-sm font-bold text-slate-900 dark:text-white">Draft Composer</p>
                  </div>
                  <div className="flex items-center gap-[2px] text-slate-600 dark:text-slate-300">
                    <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100"><strong className="text-[11px] font-semibold">B</strong></button>
                    <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100"><em className="text-[11px]">I</em></button>
                    <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100"><List size={12} strokeWidth={1.6} /></button>
                    <div className="mx-[3px] h-3.5 w-px bg-slate-200" />
                    <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100"><Link2 size={12} strokeWidth={1.6} /></button>
                  </div>
                  <div className="flex items-center gap-1.5">
                  <motion.button
                    type="button"
                    onClick={() => setDraftBody(current.draft_body)}
                    {...microInteractionMotion}
                    className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#E2E8F0] bg-white px-3 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                  >
                    <CircleHelp size={12} strokeWidth={1.7} />
                    Revert to Original
                  </motion.button>
                  <motion.button
                    type="button"
                    onClick={() => {
                      setDraftBody((prev) => `${prev}\n\nI can also share specific Cloud Infrastructure outcomes to support this request.`)
                      if (!isDraftVariant(urlVariant)) {
                        setFlowVariant((prev) => (prev === 'base-1' ? 'base-2' : prev))
                      }
                    }}
                    {...microInteractionMotion}
                    className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#44cfc0] bg-[#6bd8cb] px-2.5 text-[11px] font-semibold text-[#005049]"
                  >
                    <CheckCircle2 size={12} strokeWidth={1.7} />
                    AI Refine
                  </motion.button>
                </div>
                </div>
                <textarea
                  value={draftBody}
                  onChange={(event) => setDraftBody(event.target.value)}
                  aria-label="Draft editor"
                  className={`${dashboardUi.composerSurface} min-h-[720px] bg-white p-8 text-[14px] leading-[1.55]`}
                />
                <div className="sticky bottom-0 z-10 flex h-14 items-center justify-between border-t border-[#E2E8F0] bg-white px-6 dark:border-slate-700 dark:bg-slate-900">
                  <button type="button" onClick={() => current && setDraftBody(current.draft_body)} className="inline-flex h-7 items-center rounded-[2px] border border-[#E2E8F0] bg-white px-4 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                    Cancel
                  </button>
                  <div className="flex items-center gap-3">
                    <motion.button
                      type="button"
                      onClick={() => {
                        if (!isDraftVariant(urlVariant)) setFlowVariant('whatif-1')
                        persistDraftState()
                        setAutosaveState('saved')
                        setLastSavedAt(Date.now())
                        setActionToast({ kind: 'success', message: 'Draft progress saved.' })
                      }}
                      {...microInteractionMotion}
                      className="inline-flex h-7 items-center rounded-[2px] border border-[#E2E8F0] bg-white px-4 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                    >
                      Save as Draft
                    </motion.button>
                    <motion.button type="button" onClick={() => void submitApproval()} disabled={!current || submitting !== null} {...microInteractionMotion} className="inline-flex h-7 items-center gap-2 rounded-[2px] bg-[#00685f] px-6 text-[11px] font-semibold text-white disabled:opacity-60">
                      {submitting === 'approve' ? <Loader2 size={12} className="animate-spin" /> : null}
                      {approveButtonLabel}
                    </motion.button>
                    <motion.button type="button" onClick={() => void rejectApproval()} disabled={!current || submitting !== null} {...microInteractionMotion} className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#d9e1dd] bg-white px-2.5 text-[11px] font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 disabled:opacity-60">
                      {submitting === 'reject' ? <Loader2 size={12} className="animate-spin" /> : <X size={12} />}
                      Reject
                    </motion.button>
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
                <motion.div variants={motionEnabled ? fadeInUpVariants : undefined} className={`${dashboardUi.utilityCard} !rounded-[2px] border-[#d9e1dd] p-3 dark:border-slate-700`}>
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
                </motion.div>
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
    </motion.div>
  )
}
