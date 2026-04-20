'use client'

import { useState } from 'react'
import { Check, X, Edit3, Mail, LinkIcon, Loader2, ShieldCheck, AlertCircle } from 'lucide-react'
import { cn, channelLabel, relativeTime } from '@/lib/utils'
import { useApprovals } from '@/hooks/useApprovals'
import { useApprovalStore } from '@/stores/approvalStore'
import { approvalsApi } from '@/lib/api'
import type { Approval } from '@/types'

function ChannelIcon({ channel }: { channel: Approval['channel'] }) {
  if (channel === 'email') return <Mail size={12} />
  if (channel === 'linkedin') return <LinkIcon size={12} />
  return null
}

function ApprovalCard({ approval }: { approval: Approval }) {
  const { removeApproval, updateApproval } = useApprovalStore()
  const [editing, setEditing] = useState(false)
  const [editedBody, setEditedBody] = useState(approval.draft_body)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [done, setDone] = useState<'approved' | 'rejected' | null>(null)

  async function handleApprove() {
    setApproving(true)
    try {
      await approvalsApi.approve(approval.id, editing ? editedBody : undefined)
      setDone('approved')
      setTimeout(() => removeApproval(approval.id), 1200)
    } catch {
      setApproving(false)
    }
  }

  async function handleReject() {
    setRejecting(true)
    try {
      await approvalsApi.reject(approval.id)
      setDone('rejected')
      setTimeout(() => removeApproval(approval.id), 800)
    } catch {
      setRejecting(false)
    }
  }

  if (done) {
    return (
      <div className={cn(
        'card p-4 flex items-center gap-3 animate-fade-in transition-all',
        done === 'approved' ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-rose-500/30 bg-rose-500/10'
      )}>
        {done === 'approved' ? <Check size={16} className="text-emerald-300" /> : <X size={16} className="text-rose-300" />
        }
        <p className="text-sm font-medium text-zinc-200">
          {done === 'approved' ? `Application to ${approval.application.job.company} queued for send` : 'Rejected'}
        </p>
      </div>
    )
  }

  return (
    <div className="card animate-fade-in">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900 text-xs font-semibold text-zinc-300">
              {approval.application.job.company.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-100">{approval.application.job.company}</p>
              <p className="text-xs text-zinc-400">{approval.application.job.title}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              'badge text-xs gap-1',
              approval.channel === 'email' ? 'ch-email' : 'ch-linkedin'
            )}>
              <ChannelIcon channel={approval.channel} />
              {channelLabel(approval.channel)}
            </span>
            <span className="text-2xs text-zinc-500">{relativeTime(approval.created_at)}</span>
          </div>
        </div>

        {/* Subject */}
        {approval.subject && (
          <div className="mb-2">
            <span className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Subject </span>
            <span className="text-xs text-zinc-300">{approval.subject}</span>
          </div>
        )}

        {/* Draft preview / edit */}
        <div className="mb-3 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
          {editing ? (
            <textarea
              value={editedBody}
              onChange={(e) => setEditedBody(e.target.value)}
              className="min-h-[140px] w-full resize-none bg-transparent p-3 text-xs leading-relaxed text-zinc-300 focus:outline-none"
            />
          ) : (
            <div className="p-3 relative">
              <p className="line-clamp-5 whitespace-pre-wrap text-xs leading-relaxed text-zinc-300">
                {approval.draft_body}
              </p>
              <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-zinc-950 to-transparent" />
            </div>
          )}
        </div>

        {/* HITL notice */}
        <div className="flex items-center gap-1.5 mb-3 px-1">
          <ShieldCheck size={12} className="text-emerald-300" />
          <p className="text-2xs text-zinc-500">
            Nothing is sent until you approve. You can edit before approving.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleApprove}
            disabled={approving || rejecting}
            className="btn btn-primary text-xs gap-1.5"
          >
            {approving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
            {approving ? 'Sending…' : 'Approve & send'}
          </button>
          <button
            onClick={() => setEditing((x) => !x)}
            className={cn('btn text-xs gap-1.5', editing && 'border-zinc-700 bg-zinc-900')}
          >
            <Edit3 size={12} />
            {editing ? 'Done editing' : 'Edit draft'}
          </button>
          <button
            onClick={handleReject}
            disabled={approving || rejecting}
            className="btn btn-danger text-xs gap-1.5 ml-auto"
          >
            {rejecting ? <Loader2 size={12} className="animate-spin" /> : <X size={12} />}
            Reject
          </button>
        </div>
      </div>
    </div>
  )
}

function ApprovalSkeleton() {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex gap-3">
        <div className="skeleton w-9 h-9 rounded-md flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-3.5 w-32 rounded" />
          <div className="skeleton h-3 w-24 rounded" />
        </div>
        <div className="skeleton h-5 w-16 rounded-full" />
      </div>
      <div className="skeleton h-28 rounded-lg" />
      <div className="flex gap-2">
        <div className="skeleton h-7 w-32 rounded-md" />
        <div className="skeleton h-7 w-20 rounded-md" />
        <div className="skeleton h-7 w-16 rounded-md ml-auto" />
      </div>
    </div>
  )
}

export default function ApprovalsPage() {
  const { approvals, loading } = useApprovalStore()
  useApprovals()

  const pending = approvals.filter((a) => a.status === 'pending')

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <section className="rounded-3xl border border-zinc-800 bg-[#080808] p-5 sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Approvals</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Pending approvals</h1>
        <p className="mt-2 text-sm text-zinc-400 sm:text-base">Review AI-drafted applications before they are sent</p>
      </section>

      {/* Notice */}
      {pending.length > 0 && (
        <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5">
          <AlertCircle size={15} className="mt-0.5 flex-shrink-0 text-emerald-300" />
          <p className="text-sm text-emerald-200">
            <span className="font-medium">{pending.length} application{pending.length !== 1 ? 's' : ''} ready for review.</span>{' '}
            AI drafted each one — nothing is sent until you approve.
          </p>
        </div>
      )}

      {/* List */}
      <div className="space-y-3">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <ApprovalSkeleton key={i} />)
          : pending.length === 0
          ? (
            <div className="text-center py-16">
              <ShieldCheck size={28} className="mx-auto mb-3 text-emerald-300 opacity-60" />
              <p className="text-sm font-medium text-zinc-300">All caught up</p>
              <p className="mt-1 text-xs text-zinc-500">No pending approvals right now</p>
            </div>
          )
          : pending.map((a) => <ApprovalCard key={a.id} approval={a} />)
        }
      </div>
    </div>
  )
}
