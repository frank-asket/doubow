'use client'

import { useEffect, useState } from 'react'
import { Check, X, Edit3, Mail, LinkIcon, Loader2, ShieldCheck, AlertCircle } from 'lucide-react'
import { DashboardPageHeader } from '../../components/dashboard/DashboardPageHeader'
import { cn, channelLabel, relativeTime } from '../../lib/utils'
import { useApprovals } from './useApprovals'
import { useApprovalStore } from './approvalStore'
import { ApiError, approvalsApi, googleIntegrationsApi, linkedinIntegrationsApi } from '../../lib/api'
import type { Approval } from '@doubow/shared'

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
  const isEmail = approval.channel === 'email'
  const isLinkedIn = approval.channel === 'linkedin'

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
      <div
        className={cn(
          'card flex animate-fade-in items-center gap-3 p-4 transition-all',
          done === 'approved'
            ? 'border-emerald-200 bg-emerald-50'
            : 'border-zinc-200 bg-zinc-100',
        )}
      >
        {done === 'approved' ? (
          <Check size={16} className="text-emerald-700" />
        ) : (
          <X size={16} className="text-zinc-600" />
        )}
        <p className="text-sm font-medium text-zinc-800">
          {done === 'approved' ? `Application to ${approval.application.job.company} queued for send` : 'Rejected'}
        </p>
      </div>
    )
  }

  return (
    <div className="card animate-fade-in">
      <div className="p-4">
        {/* Header */}
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md border border-indigo-100 bg-indigo-50 text-xs font-semibold text-indigo-800">
              {approval.application.job.company.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-900">{approval.application.job.company}</p>
              <p className="text-xs text-zinc-500">{approval.application.job.title}</p>
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
            <span className="text-2xs text-zinc-400">{relativeTime(approval.created_at)}</span>
          </div>
        </div>

        {/* Subject */}
        {approval.subject && (
          <div className="mb-2">
            <span className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Subject </span>
            <span className="text-xs text-zinc-700">{approval.subject}</span>
          </div>
        )}

        {/* Draft preview / edit */}
        <div className="mb-3 overflow-hidden rounded-[12px] border border-zinc-200 bg-zinc-50">
          {editing ? (
            <textarea
              value={editedBody}
              onChange={(e) => setEditedBody(e.target.value)}
              className="min-h-[140px] w-full resize-none bg-white p-3 text-xs leading-relaxed text-zinc-800 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
          ) : (
            <div className="relative p-3">
              <p className="line-clamp-5 whitespace-pre-wrap text-xs leading-relaxed text-zinc-700">
                {approval.draft_body}
              </p>
              <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-zinc-50 to-transparent" />
            </div>
          )}
        </div>

        {/* HITL notice */}
        <div className="mb-3 flex items-center gap-1.5 px-1">
          <ShieldCheck size={12} className="text-indigo-600" />
          <p className="text-2xs text-zinc-500">
            {isEmail
              ? 'Nothing is sent until you approve. You can edit before approving.'
              : isLinkedIn
              ? 'Approve to queue the LinkedIn handoff. You can still edit before approving.'
              : 'Approve to queue handoff. You can edit before approving.'}
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
            {approving ? 'Queuing…' : isEmail ? 'Approve & queue email' : isLinkedIn ? 'Approve & queue LinkedIn' : 'Approve'}
          </button>
          <button
            onClick={() => setEditing((x) => !x)}
            className={cn(
              'btn text-xs gap-1.5',
              editing && 'border-indigo-200 bg-indigo-50 text-indigo-900',
            )}
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
  const [gmailConnected, setGmailConnected] = useState<boolean | null>(null)
  const [linkedinConnected, setLinkedinConnected] = useState<boolean | null>(null)
  const [integrationBusy, setIntegrationBusy] = useState(false)
  const [integrationError, setIntegrationError] = useState<string | null>(null)

  const pending = approvals.filter((a) => a.status === 'pending')
  const pendingEmail = pending.some((a) => a.channel === 'email')
  const pendingLinkedIn = pending.some((a) => a.channel === 'linkedin')

  async function refreshIntegrationStatus() {
    setIntegrationError(null)
    try {
      const [gmail, linkedin] = await Promise.all([
        googleIntegrationsApi.status().catch(() => ({ connected: false, google_email: null })),
        linkedinIntegrationsApi.status().catch(() => ({ connected: false, expires_at: null })),
      ])
      setGmailConnected(Boolean(gmail.connected))
      setLinkedinConnected(Boolean(linkedin.connected))
    } catch {
      setIntegrationError('Could not refresh channel connection status.')
    }
  }

  async function connectGoogle() {
    setIntegrationBusy(true)
    setIntegrationError(null)
    try {
      const { authorization_url } = await googleIntegrationsApi.getAuthorizationUrl()
      window.location.href = authorization_url
    } catch (e) {
      if (e instanceof ApiError) setIntegrationError(e.detail)
      else setIntegrationError('Could not start Google connect flow.')
    } finally {
      setIntegrationBusy(false)
    }
  }

  async function connectLinkedIn() {
    setIntegrationBusy(true)
    setIntegrationError(null)
    try {
      const { authorization_url } = await linkedinIntegrationsApi.getAuthorizationUrl()
      window.location.href = authorization_url
    } catch (e) {
      if (e instanceof ApiError) setIntegrationError(e.detail)
      else setIntegrationError('Could not start LinkedIn connect flow.')
    } finally {
      setIntegrationBusy(false)
    }
  }

  useEffect(() => {
    void refreshIntegrationStatus()
  }, [pendingEmail, pendingLinkedIn])

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <DashboardPageHeader
        kicker="Approvals"
        title="Pending approvals"
        description="Review AI-drafted applications before they are sent"
      />

      {/* Notice */}
      {pending.length > 0 && (
        <div className="mb-5 flex items-start gap-2.5 rounded-[16px] border border-indigo-100 bg-indigo-50/90 p-3.5">
          <AlertCircle size={15} className="mt-0.5 flex-shrink-0 text-indigo-600" />
          <p className="text-sm text-indigo-950">
            <span className="font-medium">{pending.length} application{pending.length !== 1 ? 's' : ''} ready for review.</span>{' '}
            AI drafted each one — nothing is sent until you approve.
          </p>
        </div>
      )}

      {(pendingEmail || pendingLinkedIn) && (
        <div className="rounded-[16px] border border-zinc-200 bg-white p-3.5">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-zinc-900">Channel handoff status</p>
            <button
              type="button"
              onClick={() => void refreshIntegrationStatus()}
              className="btn text-xs"
              disabled={integrationBusy}
            >
              Refresh status
            </button>
          </div>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {pendingEmail && (
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs font-medium text-zinc-800">Gmail (email approvals)</p>
                <p className="mt-1 text-xs text-zinc-500">
                  {gmailConnected === null
                    ? 'Checking status...'
                    : gmailConnected
                    ? 'Connected'
                    : 'Not connected'}
                </p>
                {!gmailConnected && (
                  <button type="button" onClick={() => void connectGoogle()} className="btn mt-2 text-xs" disabled={integrationBusy}>
                    Connect Gmail
                  </button>
                )}
              </div>
            )}
            {pendingLinkedIn && (
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs font-medium text-zinc-800">LinkedIn (note approvals)</p>
                <p className="mt-1 text-xs text-zinc-500">
                  {linkedinConnected === null
                    ? 'Checking status...'
                    : linkedinConnected
                    ? 'Connected'
                    : 'Not connected'}
                </p>
                {!linkedinConnected && (
                  <button type="button" onClick={() => void connectLinkedIn()} className="btn mt-2 text-xs" disabled={integrationBusy}>
                    Connect LinkedIn
                  </button>
                )}
              </div>
            )}
          </div>
          {integrationError && <p className="mt-2 text-xs text-red-700">{integrationError}</p>}
        </div>
      )}

      {/* List */}
      <div className="space-y-3">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <ApprovalSkeleton key={i} />)
          : pending.length === 0
          ? (
            <div className="py-16 text-center">
              <ShieldCheck size={28} className="mx-auto mb-3 text-emerald-500" />
              <p className="text-sm font-medium text-zinc-800">All caught up</p>
              <p className="mt-1 text-xs text-zinc-500">No pending approvals right now</p>
            </div>
          )
          : pending.map((a) => <ApprovalCard key={a.id} approval={a} />)
        }
      </div>
    </div>
  )
}
