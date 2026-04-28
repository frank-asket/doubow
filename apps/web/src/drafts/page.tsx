'use client'

import { useEffect, useMemo, useState } from 'react'
import { Bold, History, Italic, Link2, List, Loader2, Sparkles } from 'lucide-react'
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

  if (!current) {
    return (
      <div className="p-6">
        <div className="rounded-[2px] border border-[#E2E8F0] bg-white p-6 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
          No pending drafts available yet.
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-56px)] bg-[#f0f5f2] dark:bg-slate-950">
      {toast ? (
        <div className="fixed left-1/2 top-[66px] z-50 -translate-x-1/2 rounded-[2px] border border-[#E2E8F0] bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
          {toast}
        </div>
      ) : null}
      <header className="flex h-12 items-center gap-3 border-b border-[#E2E8F0] bg-white px-6 dark:border-slate-700 dark:bg-slate-900">
        <p className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">OfferRefine HITL</p>
        <span className="h-4 w-px bg-slate-200 dark:bg-slate-700" />
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Request Change: {current.application.job.company} {current.application.job.title}
        </p>
      </header>

      <div className="grid grid-cols-12 gap-4 p-6">
        <section className="col-span-8 flex min-h-[640px] flex-col rounded-[2px] border border-[#E2E8F0] bg-white dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-[#E2E8F0] bg-slate-50/50 p-2 dark:border-slate-700 dark:bg-slate-900/60">
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
                onClick={() => setDraftBody(current.draft_body)}
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
            className="min-h-[720px] flex-1 resize-none border-none bg-white p-8 text-[14px] leading-[1.55] text-slate-900 focus:outline-none dark:bg-slate-900 dark:text-slate-100"
          />
        </section>

        <aside className="col-span-4 space-y-4">
          <div className="rounded-[2px] border border-[#E2E8F0] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Offer Snapshot</h3>
            <div className="space-y-3 text-[13px]">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2 dark:border-slate-700"><span className="text-slate-500">Base Salary</span><span className="font-semibold">{current.application.job.salary_range || 'N/A'}</span></div>
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2 dark:border-slate-700"><span className="text-slate-500">Channel</span><span className="font-semibold">{current.channel}</span></div>
              <div className="flex items-center justify-between pt-1"><span className="font-medium text-slate-800 dark:text-slate-200">Status</span><span className="font-bold text-[#00685f]">Pending</span></div>
            </div>
          </div>
          <div className="rounded-[2px] border border-[#E2E8F0] border-l-2 border-l-amber-600 bg-white p-4 text-[13px] dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wider text-amber-700">AI Feedback</h3>
            <p className="text-slate-600 dark:text-slate-300">Tone is professional and data-driven.</p>
          </div>
        </aside>
      </div>

      <footer className="sticky bottom-0 flex h-14 items-center justify-between border-t border-[#E2E8F0] bg-white px-6 dark:border-slate-700 dark:bg-slate-900">
        <button
          type="button"
          onClick={() => setDraftBody(current.draft_body)}
          className="inline-flex h-7 items-center rounded-[2px] border border-[#E2E8F0] bg-white px-4 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
        >
          Cancel
        </button>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => void saveDraft()}
            disabled={busy !== null}
            className="inline-flex h-7 items-center rounded-[2px] border border-[#E2E8F0] bg-white px-4 text-[11px] font-medium text-slate-600 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
          >
            {busy === 'save' ? <Loader2 size={12} className="animate-spin" /> : null}
            Save as Draft
          </button>
          <button
            type="button"
            onClick={() => void sendDraft()}
            disabled={busy !== null}
            className="inline-flex h-7 items-center gap-2 rounded-[2px] bg-[#00685f] px-6 text-[11px] font-semibold text-white disabled:opacity-60"
          >
            {busy === 'send' ? <Loader2 size={12} className="animate-spin" /> : null}
            Approve outreach
          </button>
        </div>
      </footer>
    </div>
  )
}

