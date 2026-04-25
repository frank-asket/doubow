'use client'

import { Bot, Briefcase, ChevronRight, CheckCircle2, Lightbulb, ListChecks, Loader2, Mic, Plus, SearchCheck, SendHorizonal, Settings, Sparkles, StopCircle, User } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { candidatePageShell, candidateTokens as tk } from '@/lib/candidateUi'
import useSWR from 'swr'
import { agentChatApi, authApi, type ChatThreadSummary, streamOrchestratorChat } from '@/lib/api'

type RoleCard = {
  title: string
  meta: string
}

type ChatMessage =
  | {
      id: string
      role: 'assistant' | 'user'
      text: string
      timeLabel?: string
      roleCards?: RoleCard[]
    }

type AgentTask = {
  id: string
  title: string
  detail: string
  tone: 'amber' | 'teal' | 'muted'
  progress?: number
}

const SUGGESTIONS = [
  'Find more remote jobs',
  'Help me prep for my next interview',
  'Update my resume',
] as const

const ROLE_CARDS: RoleCard[] = [
  { title: 'Senior Product Manager', meta: 'Stripe • Remote • $180k - $220k' },
  { title: 'Lead Strategy Lead', meta: 'Plaid • Hybrid (NY) • $165k - $200k' },
]

const AGENT_TASKS: AgentTask[] = [
  {
    id: 'search-roles',
    title: 'Searching for New Roles',
    detail: 'Scanning LinkedIn & Indeed',
    tone: 'amber',
    progress: 68,
  },
  {
    id: 'draft-writing',
    title: 'Writing Your Drafts',
    detail: 'Tailoring cover letter for Stripe',
    tone: 'teal',
  },
  {
    id: 'prep-pending',
    title: 'Interview Prep',
    detail: 'Pending user request',
    tone: 'muted',
  },
]

const ATTENTION_ITEMS = ['Review Stripe Draft', 'Schedule 1:1 Coaching'] as const
const LOCAL_STORAGE_NS = 'doubow.messages.history.v1'

function sectionIconForLine(line: string) {
  const lower = line.toLowerCase()
  if (lower.includes('next') || lower.includes('plan') || lower.includes('action')) return ListChecks
  if (lower.includes('tip') || lower.includes('idea') || lower.includes('suggest')) return Lightbulb
  return CheckCircle2
}

function renderAssistantBody(text: string, isStreaming: boolean) {
  if (!text && isStreaming) {
    return (
      <span className="inline-flex items-center gap-2 text-zinc-600 dark:text-slate-200">
        <Loader2 size={14} className="animate-spin" />
        <span className="inline-flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-teal-600 [animation:ping_1.2s_infinite]" />
          <span className="h-1.5 w-1.5 rounded-full bg-teal-600 [animation:ping_1.2s_infinite_150ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-teal-600 [animation:ping_1.2s_infinite_300ms]" />
        </span>
        Thinking...
      </span>
    )
  }

  const lines = text
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line, index, all) => line.length > 0 || (index > 0 && all[index - 1].length > 0))

  return (
    <div className="space-y-2">
      {lines.map((line, index) => {
        const isBullet = /^[-*•]\s+/.test(line)
        const isNumbered = /^\d+\.\s+/.test(line)
        const isSection = /:$/.test(line) || /^#{1,3}\s+/.test(line)
        if (isSection) {
          const Icon = sectionIconForLine(line)
          const cleaned = line.replace(/^#{1,3}\s+/, '').replace(/:$/, '')
          return (
            <p key={`${index}-${cleaned}`} className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-teal-700 dark:text-teal-300">
              <Icon size={13} />
              {cleaned}
            </p>
          )
        }
        if (isBullet || isNumbered) {
          const cleaned = line.replace(/^[-*•]\s+/, '').replace(/^\d+\.\s+/, '')
          return (
            <p key={`${index}-${cleaned}`} className="flex items-start gap-2 text-[14px] leading-relaxed text-zinc-800 dark:text-slate-100">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-600" />
              <span>{cleaned}</span>
            </p>
          )
        }
        return (
          <p key={`${index}-${line}`} className="text-[14px] leading-relaxed text-zinc-800 dark:text-slate-100">
            {line}
          </p>
        )
      })}
    </div>
  )
}

function taskToneClasses(tone: AgentTask['tone']) {
  if (tone === 'amber') {
    return {
      rail: 'bg-amber-600',
      icon: 'text-amber-700 dark:text-amber-300',
      panel: 'border-zinc-200 bg-white dark:border-slate-700 dark:bg-slate-900',
    }
  }
  if (tone === 'teal') {
    return {
      rail: 'bg-teal-600',
      icon: 'text-teal-700 dark:text-teal-300',
      panel: 'border-zinc-200 bg-white dark:border-slate-700 dark:bg-slate-900',
    }
  }
  return {
    rail: 'bg-zinc-400 dark:bg-slate-600',
    icon: 'text-zinc-500 dark:text-slate-200',
    panel: 'border-zinc-200 bg-zinc-50 dark:border-slate-700 dark:bg-slate-900',
  }
}

export default function MessagesPage() {
  const stopRef = useRef<(() => void) | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const sequenceRef = useRef(3)
  const [streaming, setStreaming] = useState(false)
  const [composer, setComposer] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [hydrated, setHydrated] = useState(false)
  const [threadListOffset, setThreadListOffset] = useState(0)
  const [threadSidebar, setThreadSidebar] = useState<ChatThreadSummary[]>([])
  const [threadsHasMore, setThreadsHasMore] = useState(false)
  const [hydratedChatThreadId, setHydratedChatThreadId] = useState<string | null>(null)
  const [hasMoreChat, setHasMoreChat] = useState(false)
  const [loadingOlder, setLoadingOlder] = useState(false)

  const marketMessage = useMemo(
    () =>
      'While you were away, new roles matched your saved criteria. I can list them by fit, channel, or location—or help draft a follow-up for an application you already sent.',
    [],
  )

  const initialMessages = useMemo<ChatMessage[]>(() => [
    { id: 'm1', role: 'assistant', text: marketMessage, timeLabel: 'Today, 10:24 AM' },
    {
      id: 'm2',
      role: 'user',
      text: "Let's look at those remote roles first. Can you highlight the ones with a focus on FinTech?",
      timeLabel: '10:25 AM',
    },
    {
      id: 'm3',
      role: 'assistant',
      text: 'Searching through the latest listings... I found two that specifically mention FinTech backgrounds as a preference.',
      roleCards: ROLE_CARDS,
    },
  ], [marketMessage])

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages)

  const { data: meDebug } = useSWR('messages-me-debug', authApi.meDebug, {
    shouldRetryOnError: false,
    revalidateOnFocus: false,
  })
  const localUserKey = meDebug?.user_id ? `u:${meDebug.user_id}` : 'u:anon'

  const { data: threadBatch } = useSWR(
    meDebug?.user_id ? ['messages-backend-threads', threadListOffset] : null,
    () => agentChatApi.listThreads(20, threadListOffset),
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )

  useEffect(() => {
    if (!threadBatch) return
    if (threadListOffset === 0) setThreadSidebar(threadBatch.threads)
    else setThreadSidebar((prev) => [...prev, ...threadBatch.threads])
    setThreadsHasMore(threadBatch.has_more)
  }, [threadBatch, threadListOffset])

  useEffect(() => {
    setThreadListOffset(0)
    setThreadSidebar([])
  }, [meDebug?.user_id])

  useEffect(() => {
    if (hydrated) return
    try {
      const raw = localStorage.getItem(`${LOCAL_STORAGE_NS}:${localUserKey}`)
      if (!raw) {
        setHydrated(true)
        return
      }
      const parsed = JSON.parse(raw) as {
        threadId?: string | null
        messages?: Array<{ role: 'assistant' | 'user'; text: string }>
      }
      if (Array.isArray(parsed.messages) && parsed.messages.length > 0) {
        setMessages(
          parsed.messages.map((m, i) => ({
            id: `local-${i + 1}`,
            role: m.role,
            text: m.text,
          })),
        )
      }
      if (parsed.threadId) {
        setThreadId(parsed.threadId)
      }
    } catch {
      /* ignore invalid local cache */
    } finally {
      setHydrated(true)
    }
  }, [hydrated, localUserKey])

  useEffect(() => {
    if (!hydrated) return
    const payload = {
      threadId,
      messages: messages.map((m) => ({ role: m.role, text: m.text })),
    }
    localStorage.setItem(`${LOCAL_STORAGE_NS}:${localUserKey}`, JSON.stringify(payload))
  }, [hydrated, localUserKey, messages, threadId])

  useEffect(() => {
    const candidate = threadSidebar[0]
    if (!candidate || threadId) return
    setThreadId(candidate.id)
  }, [threadSidebar, threadId])

  const { data: backendThreadDetail } = useSWR(
    meDebug?.user_id && threadId ? `messages-thread-${threadId}` : null,
    () => agentChatApi.getThread(threadId as string, { limit: 50 }),
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )

  useEffect(() => {
    setHydratedChatThreadId(null)
  }, [threadId])

  useEffect(() => {
    if (!threadId || !backendThreadDetail) return
    if (backendThreadDetail.thread.id !== threadId) return
    if (hydratedChatThreadId === threadId) return
    setMessages(
      (backendThreadDetail.messages ?? []).map((m) => ({
        id: m.id,
        role: m.role === 'assistant' ? 'assistant' : 'user',
        text: m.content,
      })),
    )
    setHasMoreChat(Boolean(backendThreadDetail.has_more_messages))
    setHydratedChatThreadId(threadId)
  }, [threadId, backendThreadDetail, hydratedChatThreadId])

  const loadOlderMessages = useCallback(async () => {
    if (!threadId || loadingOlder || !hasMoreChat || messages.length === 0) return
    const oldest = messages[0]
    setLoadingOlder(true)
    try {
      const page = await agentChatApi.getThread(threadId, {
        limit: 50,
        beforeMessageId: oldest.id,
      })
      const older: ChatMessage[] = page.messages.map((m) => ({
        id: m.id,
        role: m.role === 'assistant' ? ('assistant' as const) : ('user' as const),
        text: m.content,
      }))
      setMessages((current) => [...older, ...current])
      setHasMoreChat(Boolean(page.has_more_messages))
    } finally {
      setLoadingOlder(false)
    }
  }, [threadId, loadingOlder, hasMoreChat, messages])

  const loadMoreThreads = useCallback(() => {
    if (!threadsHasMore) return
    setThreadListOffset(threadSidebar.length)
  }, [threadsHasMore, threadSidebar.length])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, streaming])

  useEffect(() => {
    return () => stopRef.current?.()
  }, [])

  const stopStreaming = useCallback(() => {
    stopRef.current?.()
    stopRef.current = null
    setStreaming(false)
  }, [])

  const sendMessage = useCallback((raw: string) => {
    const text = raw.trim()
    if (!text || streaming) return

    setError(null)
    sequenceRef.current += 1
    const userId = `m${sequenceRef.current}`
    sequenceRef.current += 1
    const aiId = `m${sequenceRef.current}`

    setMessages((current) => [...current, { id: userId, role: 'user', text }, { id: aiId, role: 'assistant', text: '' }])
    setStreaming(true)
    setComposer('')

    let aggregate = ''
    stopRef.current = streamOrchestratorChat(
      text,
      (chunk) => {
        aggregate += chunk
        setMessages((current) =>
          current.map((m) => (m.id === aiId ? { ...m, text: aggregate } : m)),
        )
      },
      {
        threadId,
        onMeta: (meta) => {
          if (meta.thread_id && !threadId) {
            setThreadId(meta.thread_id)
          }
        },
      },
      () => {
        stopRef.current = null
        setStreaming(false)
      },
      (streamError) => {
        setMessages((current) =>
          current.map((m) =>
            m.id === aiId
              ? { ...m, text: aggregate || 'I could not answer this right now. Please try again.' }
              : m,
          ),
        )
        setError(streamError)
        stopRef.current = null
        setStreaming(false)
      },
    )
  }, [streaming, threadId])

  function onComposerSubmit(event: React.FormEvent) {
    event.preventDefault()
    sendMessage(composer)
  }

  return (
    <div className={candidatePageShell}>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_300px]">
        <section className="overflow-hidden rounded-sm border-[0.5px] bg-white shadow-sm dark:bg-slate-900" style={{ borderColor: tk.outline }}>
          <header className="flex h-14 items-center justify-between border-b border-zinc-200 px-5 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <h1 className="text-[20px] font-bold tracking-tight text-zinc-900 dark:text-white">Doubow Assistant</h1>
              <span className="rounded bg-teal-700 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                All topics
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button className="rounded p-2 text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:text-white dark:hover:bg-slate-800 dark:hover:text-white" aria-label="Notifications">
                <Sparkles size={16} />
              </button>
              <button className="rounded p-2 text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:text-white dark:hover:bg-slate-800 dark:hover:text-white" aria-label="Message settings">
                <Settings size={16} />
              </button>
            </div>
          </header>

          <div className="flex min-h-[620px] flex-col">
            <div className="flex-1 space-y-6 overflow-y-auto p-5">
              {hasMoreChat ? (
                <div className="flex justify-center">
                  <button
                    type="button"
                    onClick={() => void loadOlderMessages()}
                    disabled={loadingOlder}
                    className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-[12px] font-semibold text-zinc-600 shadow-sm hover:bg-zinc-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
                  >
                    {loadingOlder ? (
                      <span className="inline-flex items-center gap-2">
                        <Loader2 size={12} className="animate-spin" />
                        Loading earlier…
                      </span>
                    ) : (
                      'Load earlier messages'
                    )}
                  </button>
                </div>
              ) : null}
              <div className="ml-11 flex flex-wrap gap-2">
                {SUGGESTIONS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => sendMessage(item)}
                    className="rounded-full border px-4 py-1.5 text-[13px] font-bold text-[#00685f] transition-colors hover:bg-teal-50 dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700"
                    style={{ borderColor: tk.primary }}
                    disabled={streaming}
                  >
                    {item}
                  </button>
                ))}
              </div>

              {messages.map((message) => {
                const isUser = message.role === 'user'
                return (
                  <div key={message.id} className={`flex max-w-3xl gap-3 ${isUser ? 'ml-auto justify-end' : ''}`}>
                    {!isUser ? (
                      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white" style={{ backgroundColor: tk.primary }}>
                        <Bot size={14} />
                      </div>
                    ) : null}
                    <div className={`space-y-2 ${isUser ? 'text-right' : 'w-full'}`}>
                      <div
                        className={`rounded-lg px-4 py-3 text-[15px] font-medium leading-relaxed transition-all duration-200 ${
                          isUser
                            ? 'text-white'
                            : `border border-zinc-200 text-zinc-800 dark:border-slate-600 dark:text-white ${
                                streaming && message.id === messages[messages.length - 1]?.id
                                  ? 'shadow-[0_0_0_1px_rgba(13,148,136,0.25)]'
                                  : ''
                              }`
                        }`}
                        style={isUser ? { backgroundColor: tk.primary } : { backgroundColor: tk.surfaceLow }}
                      >
                        {isUser ? (
                          message.text || (streaming ? <span className="inline-flex items-center gap-2"><Loader2 size={14} className="animate-spin" />Thinking...</span> : null)
                        ) : (
                          renderAssistantBody(
                            message.text,
                            streaming && message.id === messages[messages.length - 1]?.id,
                          )
                        )}
                      </div>
                      {message.roleCards?.length ? (
                        <div className="mt-4 space-y-2">
                          {message.roleCards.map((role) => (
                            <button
                              key={role.title}
                              type="button"
                              className="group flex w-full items-center justify-between rounded border border-zinc-200 bg-white px-3 py-2 text-left transition-colors hover:border-teal-300 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-teal-500/50"
                            >
                              <div>
                                <p className="text-[14px] font-bold text-zinc-900 dark:text-white">{role.title}</p>
                                <p className="text-[12px] font-medium text-zinc-500 dark:text-slate-300">{role.meta}</p>
                              </div>
                              <ChevronRight size={14} className="text-teal-700 opacity-0 transition-opacity group-hover:opacity-100" />
                            </button>
                          ))}
                        </div>
                      ) : null}
                      {message.timeLabel ? (
                        <p className={`text-[11px] uppercase tracking-wide text-zinc-400 ${isUser ? 'pr-1' : 'pl-1'}`}>{message.timeLabel}</p>
                      ) : null}
                    </div>
                    {isUser ? (
                      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-200 text-zinc-700">
                        <User size={14} />
                      </div>
                    ) : null}
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-zinc-200 p-4 dark:border-slate-700">
              <form className="relative" onSubmit={onComposerSubmit}>
                <textarea
                  value={composer}
                  onChange={(event) => setComposer(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault()
                      sendMessage(composer)
                    }
                  }}
                  placeholder="Type a message or ask for career advice..."
                  className="field min-h-[58px] w-full resize-none border-zinc-300 bg-white pr-24 text-[14px] font-medium text-zinc-900 placeholder:text-zinc-400 dark:border-slate-600 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500"
                  disabled={streaming}
                />
                <div className="absolute bottom-3 right-3 flex items-center gap-1">
                  <button className="rounded p-2 text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:text-white dark:hover:bg-slate-800" aria-label="Voice input">
                    <Mic size={16} />
                  </button>
                  {streaming ? (
                    <button
                      type="button"
                      onClick={stopStreaming}
                      className="inline-flex h-10 items-center justify-center gap-1 rounded-full border border-amber-700 bg-amber-700 px-3 text-white transition-colors hover:bg-amber-800"
                      aria-label="Stop response"
                    >
                      <StopCircle size={14} />
                      <span className="text-xs font-semibold">Stop</span>
                    </button>
                  ) : (
                    <button
                      type="submit"
                      className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-teal-700 bg-teal-700 text-white transition-colors hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
                      aria-label="Send message"
                      disabled={!composer.trim()}
                    >
                      <SendHorizonal size={16} />
                    </button>
                  )}
                </div>
              </form>
              {error ? (
                <p className="mt-2 text-xs text-rose-600">{error}</p>
              ) : null}
            </div>
          </div>
        </section>

        <aside className="space-y-3">
          <section className="rounded-sm border border-zinc-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-zinc-500 dark:text-white">Conversations</h2>
            <div className="max-h-[280px] space-y-1.5 overflow-y-auto">
              {threadSidebar.map((thread: ChatThreadSummary) => (
                <button
                  key={thread.id}
                  type="button"
                  onClick={() => setThreadId(thread.id)}
                  className={`w-full rounded border px-2.5 py-2 text-left transition-colors ${
                    threadId === thread.id ? 'border-teal-300 bg-teal-50 dark:border-teal-500/40 dark:bg-teal-950/40' : 'border-zinc-200 bg-white hover:bg-zinc-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800'
                  }`}
                >
                  <p className="truncate text-[12px] font-bold text-zinc-800 dark:text-white">{thread.title || 'Conversation'}</p>
                  <p className="text-[11px] font-semibold text-zinc-500 dark:text-slate-300">{new Date(thread.updated_at).toLocaleString()}</p>
                </button>
              ))}
              {!threadSidebar.length ? (
                <p className="text-[12px] font-semibold text-zinc-500 dark:text-white">New conversations are created automatically when you chat.</p>
              ) : null}
              {threadsHasMore ? (
                <button
                  type="button"
                  onClick={loadMoreThreads}
                  className="w-full rounded border border-dashed border-zinc-300 py-1.5 text-[11px] font-bold text-zinc-600 hover:bg-zinc-50 dark:border-slate-600 dark:text-white dark:hover:bg-slate-800"
                >
                  Load more conversations
                </button>
              ) : null}
            </div>
          </section>

          <section className="rounded-sm border border-zinc-200 bg-zinc-50 p-3 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-3 text-[11px] font-bold uppercase tracking-[0.16em] text-zinc-500 dark:text-white">What I&apos;m Doing Now</h2>
            <div className="space-y-2.5">
              {AGENT_TASKS.map((task) => {
                const tone = taskToneClasses(task.tone)
                return (
                  <article key={task.id} className={`relative overflow-hidden rounded-sm border p-3 ${tone.panel}`}>
                    <div className={`absolute left-0 top-0 h-full w-[2px] ${tone.rail}`} />
                    <div className="flex items-start gap-2.5">
                      <SearchCheck size={16} className={tone.icon} />
                      <div className="min-w-0">
                        <p className="text-[13px] font-bold text-zinc-900 dark:text-white">{task.title}</p>
                        <p className="text-[12px] font-semibold text-zinc-500 dark:text-slate-200">{task.detail}</p>
                        {typeof task.progress === 'number' ? (
                          <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-slate-700">
                            <div className="h-full bg-amber-600" style={{ width: `${task.progress}%` }} />
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </article>
                )
              })}
            </div>
          </section>

          <section className="rounded-sm border border-zinc-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-[11px] font-bold uppercase tracking-[0.16em] text-zinc-500 dark:text-white">Market Vitality</h2>
            <div className="mt-2 flex items-end gap-1">
              <span className="text-5xl font-black leading-none" style={{ color: tk.primary }}>84</span>
              <span className="pb-1 text-[13px] font-bold text-teal-700 dark:text-teal-300">+5%</span>
            </div>
            <p className="mt-2 text-[13px] font-semibold leading-snug text-zinc-600 dark:text-white">
              Your profile visibility increased this week. Recruiters are looking at your &quot;FinTech&quot; skills.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="px-1 text-[11px] font-bold uppercase tracking-[0.16em] text-zinc-500 dark:text-white">Attention Needed</h2>
            {ATTENTION_ITEMS.map((item) => (
              <button
                key={item}
                className="flex w-full items-center justify-between rounded-sm border border-zinc-200 bg-white px-3 py-3 text-left transition-colors hover:bg-zinc-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"
              >
                <span className="inline-flex items-center gap-2 text-[13px] font-bold text-zinc-800 dark:text-white">
                  <span className="h-2 w-2 rounded-full bg-amber-600" />
                  {item}
                </span>
                <ChevronRight size={14} className="text-zinc-400 dark:text-white" />
              </button>
            ))}
          </section>

          <section className="relative h-28 overflow-hidden rounded-sm border border-zinc-200 bg-zinc-100 dark:border-slate-700 dark:bg-slate-900">
            <div className="absolute inset-0 bg-gradient-to-r from-zinc-200 to-zinc-50 dark:from-slate-800 dark:to-slate-900" />
            <div className="absolute bottom-3 left-3">
              <p className="text-[13px] font-bold text-zinc-800 dark:text-white">Application Funnel</p>
              <p className="text-[12px] font-semibold text-zinc-500 dark:text-slate-200">3 interview requests</p>
            </div>
            <Briefcase className="absolute right-3 top-3 text-zinc-300 dark:text-slate-600" size={42} />
          </section>
        </aside>
      </div>

      <button
        className="fixed bottom-5 right-5 inline-flex h-12 w-12 items-center justify-center rounded-full border border-teal-700 bg-teal-700 text-white shadow-lg transition-colors hover:bg-teal-800"
        aria-label="Create new assistant task"
      >
        <Plus size={18} />
      </button>
    </div>
  )
}
