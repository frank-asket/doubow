'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  Archive,
  BarChart3,
  Bell,
  Bold,
  FileText,
  HelpCircle,
  History,
  Italic,
  Link2,
  List,
  Loader2,
  Package,
  Plus,
  Rocket,
  Save,
  Settings,
  Shield,
  Sparkles,
  Users,
} from 'lucide-react'
import { approvalsApi } from '@/lib/api'
import { useApprovalStore } from '@/src/approvals/approvalStore'
import { useApprovals } from '@/src/approvals/useApprovals'

function draftsStorageKey(approvalId: string) {
  return `drafts:editor:${approvalId}`
}

export default function DraftsPage() {
  const { approvals, removeApproval } = useApprovalStore()
  const { refresh } = useApprovals()
  const pending = useMemo(() => approvals.filter((item) => item.status === 'pending'), [approvals])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const current = useMemo(
    () => pending.find((item) => item.id === selectedId) ?? pending[0] ?? null,
    [pending, selectedId],
  )
  const [draftBody, setDraftBody] = useState('')
  const [busy, setBusy] = useState<'send' | 'save' | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (!pending.length) {
      setSelectedId(null)
      return
    }
    if (selectedId && pending.some((p) => p.id === selectedId)) return
    setSelectedId(pending[0].id)
  }, [pending, selectedId])

  useEffect(() => {
    if (!current) {
      setDraftBody('')
      return
    }
    const key = draftsStorageKey(current.id)
    const fromStorage = typeof window !== 'undefined' ? window.localStorage.getItem(key) : null
    setDraftBody(fromStorage ?? current.draft_body)
  }, [current])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(null), 2400)
    return () => window.clearTimeout(timer)
  }, [toast])

  async function saveDraft() {
    if (!current || typeof window === 'undefined') return
    setBusy('save')
    try {
      window.localStorage.setItem(draftsStorageKey(current.id), draftBody)
      setToast('Draft saved locally.')
    } finally {
      setBusy(null)
    }
  }

  async function sendDraft() {
    if (!current) return
    setBusy('send')
    try {
      await approvalsApi.approve(current.id, draftBody)
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(draftsStorageKey(current.id))
      }
      removeApproval(current.id)
      await refresh()
      setToast('Outreach approved and queued for delivery.')
    } catch {
      setToast('Could not approve outreach right now.')
    } finally {
      setBusy(null)
    }
  }

  const hasCurrent = Boolean(current)
  const requestLabel = hasCurrent
    ? `${current.application.job.company} ${current.application.job.title}`
    : 'Google L5'
  const snapshotSalary = hasCurrent ? current.application.job.salary_range || 'N/A' : '$185,000'
  const snapshotChannel = hasCurrent ? current.channel : 'gmail'

  return (
    <div className="min-h-[calc(100vh-56px)] bg-[#f0f5f2] dark:bg-slate-950">
      {toast ? (
        <div className="fixed left-1/2 top-[66px] z-50 -translate-x-1/2 rounded-[2px] border border-[#E2E8F0] bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
          {toast}
        </div>
      ) : null}
      <aside className="fixed left-0 top-0 z-40 flex h-full w-[260px] flex-col gap-2 border-r border-[#E2E8F0] bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="mb-5 px-1">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-[2px] bg-[#00685f] text-white">
              <Rocket size={14} />
            </div>
            <div>
              <p className="text-[14px] font-bold tracking-tight text-slate-900 dark:text-white">Recruitment Ops</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">High-priority zone</p>
            </div>
          </div>
        </div>

        <button className="mb-5 inline-flex h-9 items-center justify-center gap-2 rounded-[2px] bg-[#00685f] px-3 text-xs font-semibold uppercase tracking-[0.08em] text-white transition-opacity hover:opacity-95">
          <Plus size={12} />
          New draft
        </button>

        <nav className="flex-1 space-y-1">
          <div className="flex items-center gap-3 border-l-2 border-[#00685f] bg-white px-3 py-2 text-[#00685f] dark:bg-slate-900 dark:text-teal-300">
            <FileText size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Drafts</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <FileText size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Offer library</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <Users size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Candidate flow</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <BarChart3 size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Analytics</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <Package size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Workspace</span>
          </div>
        </nav>

        <div className="space-y-1 border-t border-[#E2E8F0] pt-3 dark:border-slate-800">
          <div className="flex items-center gap-3 px-3 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <HelpCircle size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Support</span>
          </div>
          <div className="flex items-center gap-3 px-3 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <Archive size={14} />
            <span className="text-xs font-semibold uppercase tracking-[0.12em]">Archive</span>
          </div>
        </div>
      </aside>

      <main className="ml-[260px] flex min-h-[calc(100vh-56px)] flex-col">
        <header className="sticky top-0 z-30 flex h-12 items-center justify-between border-b border-[#E2E8F0] bg-white px-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center gap-4">
            <p className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Offer refinement</p>
            <span className="h-4 w-px bg-slate-200 dark:bg-slate-700" />
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Request Change: {requestLabel}
            </p>
          </div>
          <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400">
            <Bell size={16} />
            <Settings size={16} />
            <div className="h-6 w-6 rounded-full border border-[#E2E8F0] bg-slate-100 dark:border-slate-700 dark:bg-slate-800" />
          </div>
        </header>

        <div className="grid flex-1 grid-cols-12 gap-4 p-6">
          <section className="col-span-8 flex min-h-[640px] flex-col border border-[#E2E8F0] bg-white dark:border-slate-700 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] bg-slate-50/60 p-2 dark:border-slate-700 dark:bg-slate-900/60">
              <div className="flex items-center gap-[2px] text-slate-600 dark:text-slate-300">
                <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><Bold size={12} strokeWidth={1.7} /></button>
                <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><Italic size={12} strokeWidth={1.7} /></button>
                <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><List size={12} strokeWidth={1.6} /></button>
                <div className="mx-[3px] h-3.5 w-px bg-slate-200 dark:bg-slate-700" />
                <button type="button" className="rounded-[2px] p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><Link2 size={12} strokeWidth={1.6} /></button>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setDraftBody(current?.draft_body ?? '')}
                  disabled={!hasCurrent}
                  className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#E2E8F0] bg-white px-3 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                >
                  <History size={12} />
                  Revert to Original
                </button>
                <button
                  type="button"
                  onClick={() => setDraftBody((prev) => `${prev}\n\nI can share additional measurable impact if helpful.`)}
                  className="inline-flex h-7 items-center gap-1 rounded-[2px] border border-[#44cfc0] bg-[#6bd8cb] px-3 text-[11px] font-semibold text-[#005049]"
                >
                  <Sparkles size={12} />
                  AI Refine
                </button>
              </div>
            </div>
            <textarea
              value={draftBody}
              onChange={(e) => setDraftBody(e.target.value)}
              disabled={!hasCurrent}
              placeholder={
                hasCurrent
                  ? ''
                  : 'No pending drafts available yet. Once a draft is created, the full editor will be enabled here.'
              }
              className="min-h-[720px] flex-1 resize-none border-none bg-white p-8 text-[14px] leading-[1.55] text-slate-900 focus:outline-none dark:bg-slate-900 dark:text-slate-100"
            />
          </section>

          <aside className="col-span-4 space-y-4">
            <div className="border border-[#E2E8F0] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Offer Snapshot
              </h3>
              <div className="space-y-3 text-[13px]">
                <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2 dark:border-slate-700"><span className="text-slate-500">Base Salary</span><span className="font-semibold">{snapshotSalary}</span></div>
                <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2 dark:border-slate-700"><span className="text-slate-500">Channel</span><span className="font-semibold">{snapshotChannel}</span></div>
                <div className="flex items-center justify-between pt-1"><span className="font-medium text-slate-800 dark:text-slate-200">Status</span><span className="font-bold text-[#00685f]">{hasCurrent ? 'Pending' : 'Idle'}</span></div>
              </div>
            </div>
            <div className="border border-[#E2E8F0] border-l-2 border-l-amber-600 bg-white p-4 text-[13px] dark:border-slate-700 dark:bg-slate-900">
              <h3 className="mb-2 inline-flex items-center gap-1 text-[11px] font-medium uppercase tracking-wider text-amber-700">
                <Sparkles size={12} />
                AI Feedback
              </h3>
              <p className="text-slate-600 dark:text-slate-300">Tone is professional and data-driven.</p>
            </div>
            <div className="border border-[#E2E8F0] border-l-2 border-l-teal-600 bg-white p-4 text-[13px] dark:border-slate-700 dark:bg-slate-900">
              <h3 className="mb-2 inline-flex items-center gap-1 text-[11px] font-medium uppercase tracking-wider text-teal-700">
                <Shield size={12} />
                Negotiation Guardrails
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                Keep asks benchmark-aligned and anchor on measurable impact.
              </p>
            </div>
          </aside>
        </div>

        <footer className="sticky bottom-0 flex h-14 items-center justify-between border-t border-[#E2E8F0] bg-white px-6 dark:border-slate-700 dark:bg-slate-900">
          <button
            type="button"
            onClick={() => setDraftBody(current?.draft_body ?? '')}
            disabled={!hasCurrent}
            className="inline-flex h-8 items-center rounded-[2px] border border-[#E2E8F0] bg-white px-4 text-[11px] font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => void saveDraft()}
              disabled={!hasCurrent || busy !== null}
              className="inline-flex h-8 items-center gap-2 rounded-[2px] border border-[#E2E8F0] bg-white px-4 text-[11px] font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              {busy === 'save' ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
              Save as Draft
            </button>
            <button
              type="button"
              onClick={() => void sendDraft()}
              disabled={!hasCurrent || busy !== null}
              className="inline-flex h-8 items-center gap-2 rounded-[2px] bg-[#00685f] px-6 text-[11px] font-semibold text-white transition-opacity hover:opacity-95 disabled:opacity-60"
            >
              {busy === 'send' ? <Loader2 size={12} className="animate-spin" /> : null}
              Send via Gmail
            </button>
          </div>
        </footer>
      </main>
    </div>
  )
}

