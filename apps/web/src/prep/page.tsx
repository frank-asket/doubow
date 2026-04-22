'use client'

import { DashboardPageHeader } from '../../components/dashboard/DashboardPageHeader'
import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, Sparkles, Loader2, BookOpen, Building2, MessageSquare, RefreshCw } from 'lucide-react'
import { cn, relativeTime } from '../../lib/utils'
import { ApiError, applicationsApi, prepApi } from '../../lib/api'
import type { Application, PrepSession, StarStory } from '@doubow/shared'

// ── Mock data for standalone demo ─────────────────────────────────────────

const MOCK_SESSIONS: PrepSession[] = [
  {
    id: '1',
    application: {
      id: 'a1',
      user_id: 'u1',
      job: {
        id: 'j1', source: 'ashby', external_id: 'x1',
        title: 'Senior ML Engineer', company: 'Mistral AI',
        location: 'Remote · Paris', description: '', url: 'https://mistral.ai',
        discovered_at: new Date(Date.now() - 86400000 * 2).toISOString(),
      },
      status: 'pending',
      channel: 'email',
      pipeline_stage: 'approve',
      last_updated: new Date().toISOString(),
      is_stale: false,
    },
    questions: [
      'Walk me through a production RAG system you built end-to-end.',
      'How do you approach latency vs. accuracy trade-offs in retrieval?',
      'Describe a time you debugged a silent failure in an agentic pipeline.',
      'How would you improve multilingual retrieval for open-weight models?',
      'Tell me about a project where you had to own technical decisions under ambiguity.',
    ],
    star_stories: [
      {
        situation: 'Our retail client needed real-time product search across 50M vectors with sub-200ms P99 latency.',
        task: 'Design and ship a hybrid retrieval system combining dense embeddings and BM25 within 6 weeks.',
        action: 'Architected a two-stage retrieval pipeline: ANN with HNSW for recall, BM25 re-ranker for precision. Added metadata filtering at the vector level to avoid post-filter bottlenecks.',
        result: 'Achieved 178ms P99, 94% NDCG@10, and reduced infra cost 40% vs. the previous full-text system.',
        reflection: 'Should have added query-level caching from day one — we added it in sprint 3 and got another 30ms reduction.',
        tags: ['RAG', 'retrieval', 'infra', 'MLOps'],
      },
    ],
    company_brief: undefined,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: '2',
    application: {
      id: 'a2',
      user_id: 'u1',
      job: {
        id: 'j2', source: 'greenhouse', external_id: 'x2',
        title: 'AI Product Engineer', company: 'Linear',
        location: 'Remote', description: '', url: 'https://linear.app',
        discovered_at: new Date(Date.now() - 86400000 * 3).toISOString(),
      },
      status: 'interview',
      channel: 'linkedin',
      pipeline_stage: 'send_prep',
      last_updated: new Date().toISOString(),
      is_stale: false,
    },
    questions: [
      'How do you balance AI capability with product UX constraints?',
      'Describe your experience shipping AI features to non-technical users.',
      'Walk me through how you instrument and evaluate an AI feature post-launch.',
      "What's your mental model for when to fine-tune vs. prompt-engineer?",
    ],
    star_stories: [],
    company_brief: undefined,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
]

// ── Sub-components ─────────────────────────────────────────────────────────

function StarStoryCard({ story, index }: { story: StarStory; index: number }) {
  const [open, setOpen] = useState(index === 0)
  const sections: [string, string][] = [
    ['Situation', story.situation],
    ['Task', story.task],
    ['Action', story.action],
    ['Result', story.result],
    ['Reflection', story.reflection],
  ]
  return (
    <div className="overflow-hidden rounded-[12px] border border-[#e7e8ee] bg-white shadow-sm">
      <button
        onClick={() => setOpen((x) => !x)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-zinc-50"
      >
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-indigo-100 bg-indigo-50 px-2 py-0.5 text-2xs font-medium text-indigo-900">
            Story {index + 1}
          </span>
          <span className="line-clamp-1 text-xs font-medium text-zinc-800">
            {story.situation.slice(0, 64)}…
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          <div className="flex gap-1">
            {story.tags.map((t) => (
              <span key={t} className="rounded border border-zinc-200 bg-zinc-50 px-1.5 py-0.5 text-2xs text-zinc-600">
                {t}
              </span>
            ))}
          </div>
          {open ? <ChevronUp size={13} className="text-zinc-500" /> : <ChevronDown size={13} className="text-zinc-500" />}
        </div>
      </button>

      {open && (
        <div className="animate-slide-up divide-y divide-zinc-100 border-t border-zinc-100">
          {sections.map(([label, text]) => (
            <div key={label} className="px-4 py-3 flex gap-3">
              <span className="w-20 flex-shrink-0 pt-0.5 text-2xs font-semibold uppercase tracking-wider text-zinc-500">
                {label}
              </span>
              <p className="text-xs leading-relaxed text-zinc-700">{text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function QuestionList({ questions }: { questions: string[] }) {
  return (
    <div className="space-y-2">
      {questions.map((q, i) => (
        <div
          key={i}
          className="flex items-start gap-3 rounded-[10px] border border-[#e7e8ee] bg-white px-4 py-3 shadow-sm transition-colors hover:border-indigo-200 hover:bg-indigo-50/50"
        >
          <span className="w-5 flex-shrink-0 text-xs font-semibold tabular-nums text-indigo-700">
            Q{i + 1}
          </span>
          <p className="text-xs leading-relaxed text-zinc-700">{q}</p>
        </div>
      ))}
    </div>
  )
}

type Tab = 'questions' | 'stories' | 'brief'
type AssistCapability = 'checking' | 'available' | 'missing' | 'error' | 'llm_missing'

function PrepSessionCard({ session, assistCapability }: { session: PrepSession; assistCapability: AssistCapability }) {
  const [activeTab, setActiveTab] = useState<Tab>('questions')
  const [generatingStory, setGeneratingStory] = useState(false)
  const [generatingBrief, setGeneratingBrief] = useState(false)
  const [storyOutput, setStoryOutput] = useState('')
  const [briefOutput, setBriefOutput] = useState(session.company_brief ?? '')
  const [localStories, setLocalStories] = useState<StarStory[]>(session.star_stories)
  const [assistError, setAssistError] = useState<string | null>(null)

  async function generateStarStory() {
    setAssistError(null)
    setGeneratingStory(true)
    setActiveTab('stories')
    setStoryOutput('')
    try {
      const { text } = await prepApi.assist(session.application.id, 'star_story')
      setStoryOutput(text)
    } catch (e) {
      const msg =
        e instanceof ApiError && e.status === 404
          ? 'Prep assist endpoint is unavailable (404). Restart backend and verify /v1/me/prep/assist exists.'
          : e instanceof ApiError
            ? e.detail
            : 'Could not generate story.'
      setAssistError(msg)
    } finally {
      setGeneratingStory(false)
    }
  }

  async function generateBrief() {
    setAssistError(null)
    setGeneratingBrief(true)
    setActiveTab('brief')
    setBriefOutput('')
    try {
      const { text } = await prepApi.assist(session.application.id, 'company_brief')
      setBriefOutput(text)
    } catch (e) {
      const msg =
        e instanceof ApiError && e.status === 404
          ? 'Prep assist endpoint is unavailable (404). Restart backend and verify /v1/me/prep/assist exists.'
          : e instanceof ApiError
            ? e.detail
            : 'Could not generate brief.'
      setAssistError(msg)
    } finally {
      setGeneratingBrief(false)
    }
  }

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: 'questions', label: 'Questions', count: session.questions.length },
    { key: 'stories', label: 'STAR-R stories', count: localStories.length },
    { key: 'brief', label: 'Company brief' },
  ]

  return (
    <div className="card animate-fade-in">
      {/* Card header */}
      <div className="border-b border-zinc-100 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md border border-indigo-100 bg-indigo-50 text-xs font-semibold text-indigo-800">
              {session.application.job.company.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-900">{session.application.job.company}</p>
              <p className="text-xs text-zinc-500">{session.application.job.title}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              'badge text-xs',
              session.application.status === 'interview' ? 'badge-interview' : 'badge-pending'
            )}>
              {session.application.status}
            </span>
            <span className="text-2xs text-zinc-500">{relativeTime(session.created_at)}</span>
          </div>
        </div>
      </div>

      {assistError && (
        <div
          role="alert"
          className="mx-4 mt-3 rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-900"
        >
          {assistError}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-zinc-100 bg-zinc-50/90 p-3">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex items-center gap-1.5 rounded-[10px] px-3 py-1.5 text-xs transition-all duration-150',
              activeTab === tab.key
                ? 'border border-indigo-200 bg-indigo-50 font-medium text-indigo-900'
                : 'text-zinc-500 hover:bg-white hover:text-zinc-800',
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="text-2xs tabular-nums text-zinc-500">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-4">
        {activeTab === 'questions' && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-zinc-500">Tailored to your resume + this JD</p>
              <button className="btn text-xs gap-1.5">
                <RefreshCw size={12} />
                Regenerate
              </button>
            </div>
            <QuestionList questions={session.questions} />
          </div>
        )}

        {activeTab === 'stories' && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-zinc-500">STAR + Reflection method</p>
              <button
                onClick={() => void generateStarStory()}
                disabled={
                  generatingStory ||
                  assistCapability === 'missing' ||
                  assistCapability === 'error' ||
                  assistCapability === 'llm_missing'
                }
                className="btn btn-primary text-xs gap-1.5"
              >
                {generatingStory ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                {generatingStory ? 'Generating…' : 'Generate story'}
              </button>
            </div>

            {localStories.length > 0 && (
              <div className="space-y-2 mb-4">
                {localStories.map((s, i) => <StarStoryCard key={i} story={s} index={i} />)}
              </div>
            )}

            {(generatingStory || storyOutput) && (
              <div className="animate-fade-in rounded-[12px] border border-[#e7e8ee] bg-zinc-50 p-4 text-xs leading-relaxed whitespace-pre-wrap text-zinc-800">
                {storyOutput}
                {generatingStory && (
                  <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-indigo-400 align-middle" />
                )}
              </div>
            )}

            {!localStories.length && !storyOutput && !generatingStory && (
              <div className="py-10 text-center text-zinc-500">
                <MessageSquare size={24} className="mx-auto mb-2 opacity-40" />
                <p className="text-xs">No stories yet — click Generate to create your first STAR-R story</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'brief' && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-zinc-500">Company intelligence for your interview</p>
              <button
                onClick={() => void generateBrief()}
                disabled={
                  generatingBrief ||
                  assistCapability === 'missing' ||
                  assistCapability === 'error' ||
                  assistCapability === 'llm_missing'
                }
                className="btn btn-primary text-xs gap-1.5"
              >
                {generatingBrief ? <Loader2 size={12} className="animate-spin" /> : <Building2 size={12} />}
                {generatingBrief ? 'Researching…' : 'Generate brief'}
              </button>
            </div>

            {(briefOutput || generatingBrief) ? (
              <div className="rounded-[12px] border border-[#e7e8ee] bg-zinc-50 p-4 text-xs leading-relaxed whitespace-pre-wrap text-zinc-800">
                {briefOutput}
                {generatingBrief && (
                  <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-indigo-400 align-middle" />
                )}
              </div>
            ) : (
              <div className="py-10 text-center text-zinc-500">
                <Building2 size={24} className="mx-auto mb-2 opacity-40" />
                <p className="text-xs">Generate a brief to see recent news, tech stack signals, and smart questions to ask</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action bar */}
      <div className="flex items-center gap-2 border-t border-zinc-100 px-4 pb-4 pt-3">
        <button
          onClick={() => void generateStarStory()}
          disabled={
            generatingStory ||
            assistCapability === 'missing' ||
            assistCapability === 'error' ||
            assistCapability === 'llm_missing'
          }
          className="btn text-xs gap-1.5"
        >
          <Sparkles size={12} />
          New STAR-R story
        </button>
        <button
          onClick={() => void generateBrief()}
          disabled={
            generatingBrief ||
            assistCapability === 'missing' ||
            assistCapability === 'error' ||
            assistCapability === 'llm_missing'
          }
          className="btn text-xs gap-1.5"
        >
          <Building2 size={12} />
          Company brief
        </button>
      </div>
    </div>
  )
}

function ApiPrepPanel({ assistCapability }: { assistCapability: AssistCapability }) {
  const [apps, setApps] = useState<Application[]>([])
  const [appId, setAppId] = useState('')
  const [session, setSession] = useState<PrepSession | null>(null)
  const [loading, setLoading] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [genError, setGenError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    applicationsApi
      .list()
      .then((r) => {
        if (cancelled) return
        setApps(r.items)
        if (r.items[0]) setAppId(r.items[0].id)
        setListLoading(false)
      })
      .catch(() => setListLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  async function onGenerate() {
    if (!appId) return
    setGenError(null)
    setLoading(true)
    try {
      const s = await prepApi.generate(appId)
      setSession(s)
    } catch (e) {
      if (e instanceof ApiError) {
        setGenError(
          e.status === 404
            ? 'That application was not found for your account—refresh the page or add a role from Discover first.'
            : e.detail || 'Prep generation failed.',
        )
      } else {
        setGenError('Prep generation failed.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (listLoading || apps.length === 0) return null

  return (
    <div className="card mb-6 border border-[#e7e8ee] p-4">
      <p className="mb-2 text-xs font-medium text-zinc-800">Generate from your applications</p>
      {assistCapability === 'missing' && (
        <div className="mb-3 rounded-[10px] border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Prep assist is unavailable on this backend instance (`/v1/me/prep/assist` returned 404). Restart/update
          the API before generating STAR-R stories or company briefs.
        </div>
      )}
      {assistCapability === 'error' && (
        <div className="mb-3 rounded-[10px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-700">
          Could not verify prep assist capability right now. You can continue, but generation may fail if the backend
          route is missing.
        </div>
      )}
      {assistCapability === 'llm_missing' && (
        <div className="mb-3 rounded-[10px] border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Prep assist route is available, but LLM is not configured on backend (`OPENROUTER_API_KEY` missing).
        </div>
      )}
      {genError && (
        <div
          role="alert"
          className="mb-3 rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-900"
        >
          {genError}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={appId}
          onChange={(e) => setAppId(e.target.value)}
          className="field max-w-[min(100%,28rem)] rounded-[10px] px-3 py-2 text-xs"
        >
          {apps.map((a) => (
            <option key={a.id} value={a.id}>
              {a.job.company} — {a.job.title}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => void onGenerate()}
          disabled={loading}
          className="btn btn-primary inline-flex items-center gap-1.5 text-xs"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : null}
          Generate prep
        </button>
      </div>
      {session && (
        <div className="mt-5">
          <PrepSessionCard session={session} assistCapability={assistCapability} />
        </div>
      )}
    </div>
  )
}

function PrepSkeleton() {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex gap-3">
        <div className="skeleton w-9 h-9 rounded-md flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-3.5 w-36 rounded" />
          <div className="skeleton h-3 w-24 rounded" />
        </div>
      </div>
      <div className="skeleton h-8 w-full rounded-lg" />
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton h-9 rounded-lg" />
        ))}
      </div>
    </div>
  )
}

export default function PrepPage() {
  const [sessions] = useState<PrepSession[]>(MOCK_SESSIONS)
  const [loading] = useState(false)
  const [assistCapability, setAssistCapability] = useState<AssistCapability>('checking')

  useEffect(() => {
    let cancelled = false
    prepApi
      .checkAssistCapability()
      .then((r) => {
        if (cancelled) return
        if (!r.available) {
          setAssistCapability('missing')
          return
        }
        setAssistCapability(r.llmConfigured ? 'available' : 'llm_missing')
      })
      .catch(() => {
        if (cancelled) return
        setAssistCapability('error')
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <DashboardPageHeader
        kicker="Interview prep"
        title="Interview prep"
        description="STAR-R stories, tailored questions, and company briefs"
        actions={
          <div className="flex items-center gap-1.5 rounded-[10px] border border-indigo-100 bg-indigo-50 px-2.5 py-1.5">
            <BookOpen size={12} className="text-indigo-600" />
            <span className="text-xs font-medium text-indigo-900">{sessions.length} sessions</span>
          </div>
        }
      />

      <ApiPrepPanel assistCapability={assistCapability} />

      {/* Info banner */}
      <div className="mb-5 flex items-start gap-2.5 rounded-[16px] border border-indigo-100 bg-indigo-50/90 p-3.5">
        <Sparkles size={14} className="mt-0.5 flex-shrink-0 text-indigo-600" />
        <p className="text-xs text-indigo-950">
          <span className="font-medium">Prep is tailored per application.</span>{' '}
          Questions and STAR-R stories are generated from your resume + the specific job description.
        </p>
      </div>
      {assistCapability === 'checking' && (
        <div className="mb-5 rounded-[12px] border border-zinc-200 bg-white px-3 py-2 text-xs text-zinc-600">
          Checking backend prep assist capability…
        </div>
      )}

      {/* Sessions */}
      <div className="space-y-4">
        {loading
          ? Array.from({ length: 2 }).map((_, i) => <PrepSkeleton key={i} />)
          : sessions.length === 0
          ? (
            <div className="py-16 text-center text-zinc-500">
              <BookOpen size={28} className="mx-auto mb-3 text-zinc-300" />
              <p className="text-sm font-medium text-zinc-800">No prep sessions yet</p>
              <p className="text-xs mt-1">Prep sessions are created when you queue an application</p>
            </div>
          )
          : sessions.map((s) => (
            <PrepSessionCard key={s.id} session={s} assistCapability={assistCapability} />
          ))
        }
      </div>
    </div>
  )
}
