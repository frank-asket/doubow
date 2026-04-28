'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Loader2, RefreshCw, Zap, AlertTriangle, RotateCcw } from 'lucide-react'
import useSWR from 'swr'
import { DashboardPageHeader } from '../../components/dashboard/DashboardPageHeader'
import { candidatePageShell } from '../../lib/candidateUi'
import { cn } from '../../lib/utils'
import { motion, useReducedMotion, fadeInUpVariants, staggerContainerVariants, getMicroInteractionMotion } from '../../lib/motion'
import { autopilotApi, ApiError } from '../../lib/api'
import { useAgentStream, useOrchestratorChat } from './useAgentStream'
import { useAgentStore } from './agentStore'
import type { AgentState, AutopilotRun } from '@doubow/shared'

const AGENT_META: Record<string, { icon: string; color: string }> = {
  discovery: { icon: '🔍', color: 'border border-teal-100 bg-teal-50 text-teal-900' },
  scorer: { icon: '◆', color: 'border border-zinc-200 bg-zinc-100 text-zinc-800' },
  tailor: { icon: '✂', color: 'border border-teal-100 bg-teal-50 text-teal-900' },
  writer: { icon: '✏', color: 'border border-zinc-200 bg-zinc-100 text-zinc-800' },
  apply: { icon: '📤', color: 'border border-zinc-200 bg-zinc-100 text-zinc-800' },
  prep: { icon: '🎯', color: 'border border-teal-100 bg-teal-50 text-teal-900' },
  monitor: { icon: '⚙', color: 'border border-zinc-200 bg-zinc-100 text-zinc-800' },
  orchestrator: { icon: '⊕', color: 'border border-teal-100 bg-teal-50 text-teal-900' },
}

const SUGGESTED_PROMPTS = [
  'What are my best opportunities right now?',
  'Why did a score drop recently?',
  'Draft a follow-up for my latest application',
  'What\'s stale in my pipeline?',
]

function StatusDot({ status }: { status: AgentState['status'] }) {
  return (
    <span
      className={cn(
        'h-2 w-2 flex-shrink-0 rounded-full',
        status === 'running' && 'animate-pulse bg-teal-400',
        status === 'active' && 'bg-emerald-500',
        status === 'idle' && 'bg-zinc-300',
        status === 'error' && 'bg-rose-500',
      )}
    />
  )
}

function AgentCard({ agent }: { agent: AgentState }) {
  const meta = AGENT_META[agent.name] ?? {
    icon: '●',
    color: 'border border-zinc-200 bg-zinc-100 text-zinc-800',
  }
  return (
    <motion.div variants={fadeInUpVariants} className="card p-3.5 flex items-start gap-3">
      <div className={cn('w-8 h-8 rounded-md flex items-center justify-center text-sm flex-shrink-0', meta.color)}>
        {meta.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-medium text-zinc-900">{agent.label}</p>
          <StatusDot status={agent.status} />
          <span className="text-2xs capitalize text-zinc-500">{agent.status}</span>
        </div>
        <p className="truncate text-xs text-zinc-600">{agent.description}</p>
        {agent.status === 'running' && agent.progress !== undefined && (
          <div className="mt-2 h-0.5 overflow-hidden rounded-full bg-zinc-200">
            <div
              className="h-full rounded-full bg-teal-500 transition-all duration-500"
              style={{ width: `${Math.round(agent.progress * 100)}%` }}
            />
          </div>
        )}
        {agent.message && (
          <p className="mt-1 truncate text-2xs text-zinc-500">{agent.message}</p>
        )}
      </div>
      {agent.items_processed !== undefined && (
        <span className="text-2xs tabular-nums text-zinc-500 flex-shrink-0">{agent.items_processed} items</span>
      )}
    </motion.div>
  )
}

function ChatMessage({ role, text }: { role: 'user' | 'ai'; text: string }) {
  return (
    <div className={cn('flex items-start gap-2.5', role === 'user' && 'flex-row-reverse')}>
      <div className={cn(
        'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0',
        role === 'ai' ? 'border border-teal-100 bg-teal-50 text-teal-900' : 'bg-zinc-200 text-zinc-900'
      )}>
        {role === 'ai' ? <Bot size={12} /> : <User size={12} />}
      </div>
      <div className={cn(
        'max-w-[80%] px-3 py-2 rounded-lg text-xs leading-relaxed',
        role === 'ai'
          ? 'border border-[#e7e8ee] bg-white dark:bg-slate-900 text-zinc-800 shadow-sm'
          : 'border border-[#e7e8ee] bg-zinc-50 text-zinc-900'
      )}>
        {text || <span className="animate-pulse opacity-60">●●●</span>}
      </div>
    </div>
  )
}

export default function AgentsPage() {
  const agents = useAgentStore((s) => s.agents)
  useAgentStream()

  const [resumeBusyRunId, setResumeBusyRunId] = useState<string | null>(null)
  const [resumeNotice, setResumeNotice] = useState<{ tone: 'ok' | 'err'; text: string } | null>(null)

  const { messages, streaming, send } = useOrchestratorChat()
  const [input, setInput] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()
  const motionEnabled = !prefersReducedMotion
  const microInteractionMotion = getMicroInteractionMotion(motionEnabled)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleSend() {
    const msg = input.trim()
    if (!msg || streaming) return
    setInput('')
    send(msg)
  }

  const activeCount = agents.filter((a) => a.status === 'active' || a.status === 'running').length
  const { data: runHistory, mutate: refreshRunHistory } = useSWR('autopilot-runs-history', () =>
    autopilotApi.listRuns(20)
  )

  const handleResumeRun = useCallback(
    async (runId: string) => {
      setResumeNotice(null)
      setResumeBusyRunId(runId)
      try {
        await autopilotApi.resumeRun(runId)
        setResumeNotice({
          tone: 'ok',
          text: 'Resume queued. Execution continues in the background.',
        })
        await refreshRunHistory()
      } catch (err) {
        const msg = err instanceof ApiError ? err.detail : 'Could not resume this run.'
        setResumeNotice({ tone: 'err', text: msg })
      } finally {
        setResumeBusyRunId(null)
      }
    },
    [refreshRunHistory],
  )

  // Fallback agents for display if SSE not yet connected
  const displayAgents: AgentState[] = agents.length > 0 ? agents : [
    { name: 'discovery', label: 'Discovery agent', description: 'Scans 45+ portals — Ashby, Greenhouse, Lever, Wellfound', status: 'active' },
    { name: 'scorer', label: 'Match scorer', description: 'Runs fit scoring (1–5) against your resume profile', status: 'running', progress: 0.6, message: 'Scoring 14 new jobs…' },
    { name: 'tailor', label: 'Resume tailor', description: 'Generates ATS-optimized resume variants per JD', status: 'active' },
    { name: 'writer', label: 'Cover letter writer', description: 'Drafts personalized cover letters and LinkedIn notes', status: 'active' },
    { name: 'apply', label: 'Apply agent', description: 'Executes channel-aware apply post-approval', status: 'idle' },
    { name: 'prep', label: 'Prep agent', description: 'Generates STAR-R questions and company briefings', status: 'active' },
    { name: 'monitor', label: 'Pipeline monitor', description: 'Deduplicates, normalizes statuses, flags stale entries', status: 'active' },
    { name: 'orchestrator', label: 'Orchestrator', description: 'Routes tasks, enforces approvals, prevents duplicate runs', status: 'running', progress: 0.3, message: 'Queuing tailor run…' },
  ]

  return (
    <motion.div
      className={candidatePageShell}
      variants={motionEnabled ? staggerContainerVariants : undefined}
      initial={motionEnabled ? 'hidden' : false}
      animate={motionEnabled ? 'visible' : undefined}
    >
      <DashboardPageHeader
        kicker="Assistant"
        title="Ask Doubow"
        description="Chat about your search and pipeline — plus what’s running in the background."
        actions={
          <>
            <div className="flex items-center gap-1.5 rounded-[10px] border border-teal-100 bg-teal-50 px-2.5 py-1.5">
              <Zap size={12} className="text-teal-800" />
              <span className="text-xs font-medium text-teal-900">
                {activeCount > 0 ? `${activeCount} task${activeCount === 1 ? '' : 's'} running` : 'Ready'}
              </span>
            </div>
            <motion.button
              type="button"
              onClick={() => {
                void refreshRunHistory()
              }}
              {...microInteractionMotion}
              className="inline-flex items-center gap-1.5 rounded-[10px] border border-[#e4e5ec] bg-white dark:bg-slate-900 px-3 py-2 text-[14px] font-medium text-zinc-700 shadow-sm hover:bg-zinc-50"
            >
              <RefreshCw size={13} />
              Refresh
            </motion.button>
          </>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Agent grid */}
        <div>
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Background activity</p>
          <div className="space-y-2">
            {displayAgents.map((agent) => (
              <AgentCard key={agent.name} agent={agent} />
            ))}
          </div>
        </div>

        {/* Orchestrator chat */}
        <div className="flex flex-col">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Chat</p>
          <div className="card flex flex-col flex-1 min-h-[520px]">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-4 py-8">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border border-teal-100 bg-teal-50">
                    <Bot size={18} className="text-teal-800" />
                  </div>
                  <p className="text-center text-xs text-zinc-500">Ask me anything about your pipeline</p>
                  <div className="grid grid-cols-1 gap-2 w-full">
                    {SUGGESTED_PROMPTS.map((p) => (
                      <motion.button
                        key={p}
                        onClick={() => send(p)}
                        {...microInteractionMotion}
                        className="rounded-[10px] border border-[#e7e8ee] bg-white dark:bg-slate-900 px-3 py-2 text-left text-xs text-zinc-700 shadow-sm transition-colors hover:border-teal-200 hover:bg-teal-50"
                      >
                        {p}
                      </motion.button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((m, i) => (
                  <ChatMessage key={i} role={m.role} text={m.text} />
                ))
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-zinc-100 bg-zinc-50/80 p-3">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  placeholder="Ask anything about your job search…"
                  className="field text-xs py-2 flex-1"
                  disabled={streaming}
                />
                <motion.button
                  onClick={handleSend}
                  disabled={!input.trim() || streaming}
                  {...microInteractionMotion}
                  className="btn btn-primary p-2 aspect-square"
                >
                  {streaming
                    ? <Loader2 size={13} className="animate-spin" />
                    : <Send size={13} />
                  }
                </motion.button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Automation history</p>
        {resumeNotice ? (
          <div
            className={cn(
              'mb-3 rounded-[10px] border px-3 py-2 text-xs',
              resumeNotice.tone === 'ok'
                ? 'border-teal-200 bg-teal-50 text-teal-900'
                : 'border-rose-200 bg-rose-50 text-rose-900',
            )}
          >
            {resumeNotice.text}
          </div>
        ) : null}
        <div className="card overflow-hidden">
          {!runHistory || runHistory.length === 0 ? (
            <div className="p-4 text-xs text-zinc-500">No runs yet.</div>
          ) : (
            <div className="divide-y divide-zinc-100">
              {runHistory.map((run: AutopilotRun) => {
                const failureMeta =
                  run.failure_code || run.failure_detail || run.failure_node
                return (
                  <div key={run.run_id}>
                    <div className="grid grid-cols-1 gap-2 p-3 text-xs sm:grid-cols-[1.5fr_0.9fr_0.8fr_1fr] sm:items-center">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-zinc-800">{run.run_id}</p>
                        <p className="mt-0.5 text-zinc-500">
                          {run.fresh_run === false ? 'Replay' : 'Fresh run'} · scope {run.scope}
                        </p>
                        {run.status === 'running' && run.resumable !== false ? (
                          <div className="mt-2">
                            <motion.button
                              type="button"
                              title="Re-enqueue if the worker stopped after saving a checkpoint (e.g. deploy or crash)."
                              onClick={() => void handleResumeRun(run.run_id)}
                              disabled={resumeBusyRunId === run.run_id}
                              {...microInteractionMotion}
                              className="inline-flex items-center gap-1.5 rounded-[8px] border border-teal-200 bg-teal-50 px-2.5 py-1 text-2xs font-semibold uppercase tracking-wide text-teal-900 shadow-sm transition-colors hover:bg-teal-100 disabled:opacity-50"
                            >
                              {resumeBusyRunId === run.run_id ? (
                                <Loader2 size={12} className="animate-spin" aria-hidden />
                              ) : (
                                <RotateCcw size={12} aria-hidden />
                              )}
                              Resume run
                            </motion.button>
                          </div>
                        ) : null}
                      </div>
                      <div>
                        <span
                          className={cn(
                            'badge text-2xs',
                            run.status === 'done'
                              ? 'badge-applied'
                              : run.status === 'failed'
                              ? 'badge-rejected'
                              : run.status === 'running'
                              ? 'badge-pending'
                              : 'badge-saved'
                          )}
                        >
                          {run.status}
                        </span>
                      </div>
                      <div className="tabular-nums text-zinc-500">
                        {run.item_results?.length ?? 0} items
                      </div>
                      <div className="text-zinc-500">
                        {(run.replayed_at ?? run.completed_at ?? run.started_at)
                          ? new Date(run.replayed_at ?? run.completed_at ?? run.started_at ?? '').toLocaleString()
                          : '—'}
                      </div>
                    </div>
                    {run.status === 'failed' && (
                      <div className="border-t border-zinc-100 bg-rose-50/50 px-3 py-2.5">
                        <div className="flex gap-2">
                          <AlertTriangle
                            className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-rose-600"
                            aria-hidden
                          />
                          <div className="min-w-0 space-y-1 text-2xs leading-snug text-rose-950">
                            <p className="font-medium text-rose-900">Run failed</p>
                            {failureMeta ? (
                              <div className="space-y-1">
                                {run.failure_code ? (
                                  <p>
                                    <span className="text-rose-700">Code </span>
                                    <span className="font-mono text-rose-900">{run.failure_code}</span>
                                  </p>
                                ) : null}
                                {run.failure_node ? (
                                  <p>
                                    <span className="text-rose-700">Node </span>
                                    <span className="font-mono text-rose-900">{run.failure_node}</span>
                                  </p>
                                ) : null}
                                {run.failure_detail ? (
                                  <p className="whitespace-pre-wrap break-words text-rose-900">
                                    <span className="text-rose-700">Detail </span>
                                    {run.failure_detail}
                                  </p>
                                ) : null}
                              </div>
                            ) : (
                              <p className="text-rose-800">
                                No structured error metadata for this run. Check server logs or retry the run.
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
