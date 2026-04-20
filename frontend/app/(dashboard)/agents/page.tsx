'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, RefreshCw, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAgentStream, useOrchestratorChat } from '@/hooks/useAgentStream'
import { useAgentStore } from '@/stores/agentStore'
import type { AgentState } from '@/types'

const AGENT_META: Record<string, { icon: string; color: string }> = {
  discovery:    { icon: '🔍', color: 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
  scorer:       { icon: '◆', color: 'border border-zinc-700 bg-zinc-900 text-zinc-300' },
  tailor:       { icon: '✂', color: 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
  writer:       { icon: '✏', color: 'border border-zinc-700 bg-zinc-900 text-zinc-300' },
  apply:        { icon: '📤', color: 'border border-zinc-700 bg-zinc-900 text-zinc-300' },
  prep:         { icon: '🎯', color: 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
  monitor:      { icon: '⚙', color: 'border border-zinc-700 bg-zinc-900 text-zinc-300' },
  orchestrator: { icon: '⊕', color: 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
}

const SUGGESTED_PROMPTS = [
  'What are my best opportunities right now?',
  'Why did a score drop recently?',
  'Draft a follow-up for my latest application',
  'What\'s stale in my pipeline?',
]

function StatusDot({ status }: { status: AgentState['status'] }) {
  return (
    <span className={cn(
      'w-2 h-2 rounded-full flex-shrink-0',
      status === 'running' && 'bg-amber-300 animate-pulse',
      status === 'active'  && 'bg-emerald-400',
      status === 'idle'    && 'bg-zinc-600',
      status === 'error'   && 'bg-rose-400',
    )} />
  )
}

function AgentCard({ agent }: { agent: AgentState }) {
  const meta = AGENT_META[agent.name] ?? { icon: '●', color: 'border border-zinc-700 bg-zinc-900 text-zinc-300' }
  return (
    <div className="card p-3.5 flex items-start gap-3">
      <div className={cn('w-8 h-8 rounded-md flex items-center justify-center text-sm flex-shrink-0', meta.color)}>
        {meta.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-medium text-zinc-100">{agent.label}</p>
          <StatusDot status={agent.status} />
          <span className="text-2xs capitalize text-zinc-500">{agent.status}</span>
        </div>
        <p className="truncate text-xs text-zinc-400">{agent.description}</p>
        {agent.status === 'running' && agent.progress !== undefined && (
          <div className="mt-2 h-0.5 overflow-hidden rounded-full bg-zinc-900">
            <div
              className="h-full rounded-full bg-emerald-400 transition-all duration-500"
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
    </div>
  )
}

function ChatMessage({ role, text }: { role: 'user' | 'ai'; text: string }) {
  return (
    <div className={cn('flex items-start gap-2.5', role === 'user' && 'flex-row-reverse')}>
      <div className={cn(
        'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0',
        role === 'ai' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-zinc-900 text-zinc-300'
      )}>
        {role === 'ai' ? <Bot size={12} /> : <User size={12} />}
      </div>
      <div className={cn(
        'max-w-[80%] px-3 py-2 rounded-lg text-xs leading-relaxed',
        role === 'ai' ? 'border border-zinc-800 bg-zinc-950 text-zinc-200' : 'bg-emerald-500 text-black'
      )}>
        {text || <span className="animate-pulse opacity-60">●●●</span>}
      </div>
    </div>
  )
}

export default function AgentsPage() {
  const agents = useAgentStore((s) => s.agents)
  useAgentStream()

  const { messages, streaming, send } = useOrchestratorChat()
  const [input, setInput] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)

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
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-3 rounded-3xl border border-zinc-800 bg-[#080808] p-5 sm:flex-row sm:items-start sm:p-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Agents</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Agent status</h1>
          <p className="mt-2 text-sm text-zinc-400 sm:text-base">Multi-agent orchestration layer</p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-1.5 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1.5">
            <Zap size={12} className="text-emerald-300" />
            <span className="text-xs font-medium text-emerald-200">{activeCount} agents active</span>
          </div>
          <button className="btn text-xs gap-1.5">
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Agent grid */}
        <div>
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Agent roster</p>
          <div className="space-y-2">
            {displayAgents.map((agent) => (
              <AgentCard key={agent.name} agent={agent} />
            ))}
          </div>
        </div>

        {/* Orchestrator chat */}
        <div className="flex flex-col">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Orchestrator chat</p>
          <div className="card flex flex-col flex-1 min-h-[520px]">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-4 py-8">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10">
                    <Bot size={18} className="text-emerald-300" />
                  </div>
                  <p className="text-center text-xs text-zinc-500">Ask me anything about your pipeline</p>
                  <div className="grid grid-cols-1 gap-2 w-full">
                    {SUGGESTED_PROMPTS.map((p) => (
                      <button
                        key={p}
                        onClick={() => send(p)}
                        className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-left text-xs text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-900"
                      >
                        {p}
                      </button>
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
            <div className="border-t border-zinc-800 p-3">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  placeholder="Ask the orchestrator…"
                  className="field text-xs py-2 flex-1"
                  disabled={streaming}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || streaming}
                  className="btn btn-primary p-2 aspect-square"
                >
                  {streaming
                    ? <Loader2 size={13} className="animate-spin" />
                    : <Send size={13} />
                  }
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
