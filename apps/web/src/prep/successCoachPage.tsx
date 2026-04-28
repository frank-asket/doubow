'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import {
  ArrowLeft,
  Building2,
  Loader2,
  Pencil,
  PlusCircle,
  Sparkles,
} from 'lucide-react'
import type { PrepSession } from '@doubow/shared'
import { DashboardPageHeader } from '../../components/dashboard/DashboardPageHeader'
import { candidatePageShell } from '../../lib/candidateUi'
import { cn, relativeTime } from '../../lib/utils'
import { usePrepSessions } from './usePrepSessions'

const SURFACE_BORDER = '#bcc9c6'
type StoryConfidence = 'low' | 'medium' | 'high'

function Mi({
  name,
  className,
}: {
  name: string
  className?: string
}) {
  return <span className={cn('material-symbols-outlined leading-none', className)}>{name}</span>
}

function questionCategory(idx: number): 'BEHAVIORAL' | 'TECHNICAL' | 'SYSTEM DESIGN' {
  if (idx === 0) return 'BEHAVIORAL'
  if (idx === 1) return 'TECHNICAL'
  return 'SYSTEM DESIGN'
}

function normalizeStoryConfidence(story: unknown): StoryConfidence {
  const confidence =
    typeof story === 'object' && story !== null && 'confidence' in story
      ? (story as { confidence?: unknown }).confidence
      : undefined
  const raw = String(confidence ?? '').toLowerCase()
  if (raw === 'low' || raw === 'medium' || raw === 'high') return raw
  return 'medium'
}

function confidenceBadge(confidence: StoryConfidence): { label: string; className: string } {
  if (confidence === 'high') return { label: 'HIGH', className: 'bg-teal-100 text-teal-800' }
  if (confidence === 'low') return { label: 'LOW', className: 'bg-amber-100 text-amber-900' }
  return { label: 'MEDIUM', className: 'bg-slate-100 text-slate-700' }
}

export default function SuccessCoachPage() {
  const searchParams = useSearchParams()
  const initialAppId = searchParams.get('applicationId') ?? undefined
  const { selectedSession, loading, generating, generateForSelected } = usePrepSessions(initialAppId)

  const company = selectedSession?.application.job.company ?? 'EcoDynamic Systems'
  const role = selectedSession?.application.job.title ?? 'Senior Product Designer'
  const questions = selectedSession?.questions.slice(0, 2) ?? [
    'Tell me about a time you had to manage a difficult stakeholder.',
    'How do you approach accessibility in complex data visualizations?',
  ]

  const stories = selectedSession?.star_stories.slice(0, 2) ?? []
  const lowConfidenceCount = stories.filter((s) => normalizeStoryConfidence(s) === 'low').length
  const requiresAction = !selectedSession || selectedSession.star_stories.length === 0

  return (
    <div className={candidatePageShell}>
      <DashboardPageHeader
        kicker="INTERVIEW PREP"
        title="Your Interview Coach"
        description={`Get ready for your upcoming interview with ${company} for the ${role} role.`}
        actions={<div className="inline-flex items-center gap-2 border border-[0.5px] bg-[#eaefed] px-3 py-1.5 text-[11px] font-semibold text-[#00685f]" style={{ borderColor: SURFACE_BORDER }}><span className="h-2 w-2 rounded-full bg-[#00685f]" />Interview in 2 days</div>}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <section className="space-y-4 lg:col-span-8">
          <article className="border border-[0.5px] bg-white dark:bg-slate-900 p-3 md:p-3" style={{ borderColor: SURFACE_BORDER }}>
            <div className="mb-3 flex items-center justify-between">
              <div className="inline-flex items-center gap-2">
                <Mi name="quiz" className="text-[14px] text-[#00685f]" />
                <h3 className="text-[16px] font-medium tracking-[-0.01em] text-[#171d1c]">Common Questions</h3>
              </div>
              <Mi name="info" className="text-[14px] text-[#3d4947]" />
            </div>
            <div className="space-y-2">
              {questions.map((q, idx) => (
                <div key={`${q}-${idx}`} className="border border-[0.5px] bg-white dark:bg-slate-900 p-3 hover:bg-[#f0f5f2]" style={{ borderColor: SURFACE_BORDER }}>
                  <div className="mb-1 flex items-center justify-between text-[11px]">
                    <span className="font-semibold tracking-[0.08em] text-[#00685f]">{questionCategory(idx)}</span>
                    <span className="text-[#3d4947]">{5 + idx * 5}-min prep</span>
                  </div>
                  <p className="text-sm font-medium text-[#171d1c]">"{q.replace(/^["']|["']$/g, '')}"</p>
                  <p className="mt-1 text-xs text-[#3d4947]">
                    {idx === 0
                      ? 'Focus on empathy and resolution. How did you align conflicting goals?'
                      : idx === 1
                        ? 'Mention standards and your practical trade-off decisions.'
                        : 'Provide a concrete architecture, trade-offs, and operating metrics.'}
                  </p>
                  <div className="mt-3 flex gap-2">
                    <button className="inline-flex h-8 items-center border border-[0.5px] border-[#00685f] bg-[#00685f] px-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-white">
                      Draft Answer
                    </button>
                    <button className="inline-flex h-8 items-center border border-[0.5px] bg-white dark:bg-slate-900 px-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#171d1c]" style={{ borderColor: SURFACE_BORDER }}>
                      View Tips
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
            <article className="space-y-3 border border-[0.5px] bg-white dark:bg-slate-900 p-3 md:col-span-5" style={{ borderColor: SURFACE_BORDER }}>
              <div className="mb-2 inline-flex items-center gap-2">
                <Building2 size={14} className="text-[#00685f]" />
                <Mi name="corporate_fare" className="text-[14px] text-[#00685f]" />
                <h3 className="text-[16px] font-medium tracking-[-0.01em] text-[#171d1c]">About the Company</h3>
              </div>
              <div className="h-32 border border-[0.5px] bg-[#dee4e1]" style={{ borderColor: SURFACE_BORDER }} />
              <div className="space-y-2 text-xs text-[#3d4947]">
                <p>
                  <span className="font-semibold text-[#171d1c]">Mission:</span> Add the employer’s stated mission from their site or annual report.
                </p>
                <p>
                  <span className="font-semibold text-[#171d1c]">Culture:</span> Summarize culture signals from primary sources (careers page, filings, reputable interviews).
                </p>
              </div>
              <p className="text-xs font-semibold text-[#00685f]">
                Read latest annual report
              </p>
            </article>

            <article className="space-y-3 border border-[0.5px] bg-white dark:bg-slate-900 p-3 md:col-span-7" style={{ borderColor: SURFACE_BORDER }}>
              <div className="mb-2 inline-flex items-center gap-2">
                <Sparkles size={14} className="text-[#00685f]" />
                <Mi name="history_edu" className="text-[14px] text-[#00685f]" />
                <h3 className="text-[16px] font-medium tracking-[-0.01em] text-[#171d1c]">Your Success Stories</h3>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {lowConfidenceCount > 0 ? (
                  <div className="sm:col-span-2 border border-[0.5px] border-amber-300 bg-amber-50 px-3 py-2">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-amber-800">
                      Manual Review Recommended
                    </p>
                    <p className="mt-1 text-xs text-amber-900">
                      {lowConfidenceCount} STAR {lowConfidenceCount > 1 ? 'stories are' : 'story is'} low confidence.
                      Add specific actions and measurable outcomes before interviews.
                    </p>
                  </div>
                ) : null}
                {(stories.length
                  ? stories
                  : [
                      {
                        tags: ['Leadership', 'Impact'],
                        situation: 'Led a team of 4 to refactor the core checkout flow.',
                        result: '15% increase in conversion rates over 3 months.',
                      },
                      {
                        tags: ['Resilience', 'Resolution'],
                        situation: 'Handled critical API outage with cross-functional teams.',
                        result: 'Maintained user trust while restoring service.',
                      },
                    ]
                ).map((story, idx) => (
                  <div key={idx} className="border border-[0.5px] p-3" style={{ borderColor: SURFACE_BORDER }}>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="bg-[#316bf3]/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-[#0051d5]">
                        {story.tags?.[0] ?? 'Story'}
                      </span>
                      <div className="inline-flex items-center gap-1.5">
                        {(() => {
                          const badge = confidenceBadge(normalizeStoryConfidence(story))
                          return (
                            <span className={cn('px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em]', badge.className)}>
                              {badge.label}
                            </span>
                          )
                        })()}
                        <Mi name="edit" className="text-[12px] text-[#3d4947]" />
                      </div>
                    </div>
                    <p className="text-xs font-semibold text-[#171d1c]">{story.situation}</p>
                    <p className="mt-1 text-xs text-[#3d4947]">{story.result}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(story.tags ?? []).slice(0, 2).map((tag) => (
                        <span key={tag} className="border border-[0.5px] px-1.5 py-0.5 text-[10px] text-[#3d4947]" style={{ borderColor: SURFACE_BORDER }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
                <button className="sm:col-span-2 inline-flex h-20 items-center justify-center gap-2 border border-[0.5px] border-dashed text-xs font-semibold text-[#3d4947] hover:border-[#00685f] hover:text-[#00685f]" style={{ borderColor: SURFACE_BORDER }}>
                  <Mi name="add_circle" className="text-[14px]" />
                  Add another story using the STAR method
                </button>
              </div>
            </article>
          </div>
        </section>

        <aside className="space-y-4 lg:col-span-4">
          <article className="border border-[0.5px] border-l-2 border-l-amber-600 bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-[16px] font-medium tracking-[-0.01em] text-[#171d1c]">Prep Status</h3>
              <span className={cn('px-2 py-0.5 text-[10px] font-semibold uppercase', requiresAction ? 'bg-amber-100 text-amber-900' : 'bg-teal-100 text-teal-900')}>
                {requiresAction ? 'Requires Action' : 'On Track'}
              </span>
            </div>
            <p className="text-xs text-[#3d4947]">
              {requiresAction
                ? "You haven't recorded a practice session for behavioral questions yet. Consistent verbal practice improves recall by 40%."
                : 'You have active prep material. Keep refining your STAR stories and role-specific question responses.'}
            </p>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#00685f]/10">
                  <Mi name="mic" className="text-[12px] text-[#00685f]" />
                </div>
                <div>
                  <p className="font-semibold text-[#171d1c]">Voice Practice</p>
                  <p className="text-[10px] text-[#3d4947]">{selectedSession?.star_stories.length ?? 0}/3 Recorded</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#00685f]/10">
                  <Mi name="fact_check" className="text-[12px] text-[#00685f]" />
                </div>
                <div>
                  <p className="font-semibold text-[#171d1c]">Company Research</p>
                  <p className="text-[10px] text-[#3d4947]">{selectedSession?.company_brief ? '80% Complete' : '0% Complete'}</p>
                </div>
              </div>
            </div>
            <button className="mt-4 inline-flex h-9 w-full items-center justify-center border border-[0.5px] border-[#00685f] bg-[#00685f] text-[11px] font-semibold uppercase tracking-[0.12em] text-white">
              Start practice interview
            </button>
            {selectedSession ? (
              <p className="mt-2 text-[10px] uppercase tracking-[0.12em] text-[#3d4947]">
                Active session updated {relativeTime(selectedSession.created_at)}
              </p>
            ) : null}
            <button
              onClick={() => void generateForSelected()}
              disabled={generating}
              className="mt-2 inline-flex h-8 w-full items-center justify-center gap-1 border border-[0.5px] text-[11px] font-semibold uppercase tracking-[0.1em] text-[#00685f] hover:bg-teal-50 disabled:opacity-70"
              style={{ borderColor: SURFACE_BORDER }}
            >
              {generating ? <Loader2 size={12} className="animate-spin" /> : null}
              Refresh Session
            </button>
            {loading ? <p className="mt-1 text-[10px] uppercase tracking-[0.12em] text-[#3d4947]">Loading session...</p> : null}
          </article>
          <Link
            href="/prep"
            className="inline-flex h-8 w-full items-center justify-center gap-1 border border-[0.5px] bg-white dark:bg-slate-900 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#171d1c] hover:bg-[#f0f5f2]"
            style={{ borderColor: SURFACE_BORDER }}
          >
            <ArrowLeft size={12} />
            Back to Prep Hub
          </Link>
        </aside>
      </div>
    </div>
  )
}
