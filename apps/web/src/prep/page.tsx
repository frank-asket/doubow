'use client'

import { useMemo, useState } from 'react'
import { Lightbulb, MessageSquareText, ShieldCheck, Zap } from 'lucide-react'
import { cn } from '../../lib/utils'
import { motion, useReducedMotion, fadeInUpVariants, staggerContainerVariants, getMicroInteractionMotion } from '../../lib/motion'
import type { PrepSession } from '@doubow/shared'
import { usePrepSessions } from './usePrepSessions'

const SURFACE_BORDER = 'rgba(109,122,119,0.38)'

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

/** Heuristic readiness from generated prep content only (no placeholder scores when session missing). */
function deriveReadiness(session: PrepSession | null): { overall: number; technical: number; cultural: number } | null {
  if (!session) return null
  const storyCount = session.star_stories.length
  const questionCount = session.questions.length
  const technical = Math.max(45, Math.min(95, 62 + questionCount * 6))
  const cultural = Math.max(42, Math.min(92, 54 + storyCount * 9))
  const overall = Math.round((technical + cultural) / 2)
  return { overall, technical, cultural }
}

function normalizeStoryConfidence(story: PrepSession['star_stories'][number]): StoryConfidence {
  const raw = String((story as { confidence?: unknown }).confidence ?? '').toLowerCase()
  if (raw === 'high' || raw === 'medium' || raw === 'low') return raw
  return 'medium'
}

function confidenceBadge(confidence: StoryConfidence): { label: string; className: string } {
  if (confidence === 'high') {
    return { label: 'HIGH', className: 'bg-teal-100 text-teal-800' }
  }
  if (confidence === 'low') {
    return { label: 'LOW', className: 'bg-amber-100 text-amber-900' }
  }
  return { label: 'MEDIUM', className: 'bg-slate-100 text-slate-700' }
}

export default function PrepPage() {
  const [situation, setSituation] = useState('')
  const [task, setTask] = useState('')
  const [action, setAction] = useState('')
  const [result, setResult] = useState('')
  const [reflection, setReflection] = useState('')
  const { selectedSession } = usePrepSessions()

  const readiness = useMemo(() => deriveReadiness(selectedSession), [selectedSession])
  const company = selectedSession?.application.job.company ?? ''
  const role = selectedSession?.application.job.title ?? ''
  const focusQuestion =
    selectedSession?.questions[0]?.replace(/^["']|["']$/g, '') ??
    'What exact steps did you take? Focus on "I" not "We".'
  const competencyTags = selectedSession?.application.score?.fit_reasons?.slice(0, 8) ?? []
  const riskFlags = selectedSession?.application.score?.risk_flags ?? []
  const starStories = selectedSession?.star_stories ?? []
  const lowConfidenceStories = starStories.filter((s) => normalizeStoryConfidence(s) === 'low')
  const briefExcerpt =
    selectedSession?.company_brief?.trim().slice(0, 220) ??
    (selectedSession?.questions[0]?.trim().slice(0, 220) ?? '')
  const prefersReducedMotion = useReducedMotion()
  const motionEnabled = !prefersReducedMotion
  const microInteractionMotion = getMicroInteractionMotion(motionEnabled)

  return (
    <motion.div
      className="mx-auto max-w-[1140px] space-y-3 px-3 py-3 sm:px-4"
      variants={motionEnabled ? staggerContainerVariants : undefined}
      initial={motionEnabled ? 'hidden' : false}
      animate={motionEnabled ? 'visible' : undefined}
    >
      <section className="border-b border-[0.5px] pb-2" style={{ borderColor: SURFACE_BORDER }}>
        <div className="mb-1 text-[10px] uppercase tracking-[0.08em] text-[#6c7774]">WORKSPACES / STAR-R BUILDER</div>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-[36px] font-medium leading-[1.05] tracking-[-0.012em] text-[#171d1c]">Interview Preparation Hub</h1>
            <p className="mt-1 text-[13px] text-[#3d4947]">Structured behavioral answer construction and technical briefing tool.</p>
          </div>
          <div className="inline-flex items-center gap-2">
            <motion.button {...microInteractionMotion} className="inline-flex h-8 items-center border border-[0.5px] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#171d1c]" style={{ borderColor: SURFACE_BORDER }}>
              EXPORT BRIEF
            </motion.button>
            <motion.button {...microInteractionMotion} className="inline-flex h-8 items-center gap-1 border border-[0.5px] border-[#008378] bg-[#00685f] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-white">
              <Mi name="add" className="text-[12px]" />
              NEW STORY
            </motion.button>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <section className="space-y-4 lg:col-span-8">
          <motion.article variants={motionEnabled ? fadeInUpVariants : undefined} className="border border-[0.5px] bg-white dark:bg-slate-900" style={{ borderColor: SURFACE_BORDER }}>
            <header className="flex items-center justify-between border-b border-[0.5px] bg-[#eaefed] px-3 py-1.5" style={{ borderColor: SURFACE_BORDER }}>
              <p className="min-w-0 truncate text-[11px] font-semibold uppercase tracking-[0.1em] text-[#3d4947]">
                {selectedSession
                  ? `STAR draft · ${selectedSession.application.job.title}`
                  : 'STAR builder — generate prep for an application to start'}
              </p>
              <span className="shrink-0 bg-teal-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-teal-800">
                {selectedSession ? 'FROM YOUR DATA' : 'EMPTY'}
              </span>
            </header>
            <div className="space-y-3 p-3">
              {[
                ['01. SITUATION', situation, setSituation, 'Set the scene. What was the context?', false],
                ['02. TASK', task, setTask, 'What was your specific responsibility?', false],
                ['03. ACTION', action, setAction, focusQuestion, true],
                ['04. RESULT', result, setResult, 'What was the outcome? Use metrics.', false],
                ['05. REFLECTION', reflection, setReflection, 'What did you learn? What would you do differently?', false],
              ].map(([label, value, setValue, placeholder, emphasized]) => (
                <section key={label as string} className={cn('border-l-2 pl-3', emphasized ? 'border-l-[#316bf3]' : 'border-l-[#dee4e1]')}>
                  <div className="mb-1.5 flex items-center justify-between">
                    <p className={cn('text-[11px] font-semibold uppercase tracking-[0.08em]', emphasized ? 'text-[#0051d5]' : 'text-[#3d4947]')}>{label as string}</p>
                    {emphasized ? <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#316bf3]">AI SUGGESTION READY</p> : null}
                  </div>
                  <textarea
                    value={value as string}
                    onChange={(e) => (setValue as (v: string) => void)(e.target.value)}
                    className={cn(
                      'h-[56px] w-full resize-none border border-[0.5px] bg-white dark:bg-slate-900 px-2.5 py-2 text-[12.5px] text-[#171d1c] outline-none',
                      emphasized ? 'border-[#316bf3]' : '',
                    )}
                    style={emphasized ? undefined : { borderColor: SURFACE_BORDER }}
                    placeholder={placeholder as string}
                  />
                  {emphasized ? (
                    <div className="mt-2 inline-flex items-center gap-1.5">
                      <button className="border border-[0.5px] border-[#9db4ff] bg-[#eef3ff] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#316bf3]">STRENGTHEN VERBS</button>
                      <button className="border border-[0.5px] border-[#9db4ff] bg-[#eef3ff] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#316bf3]">QUANTIFY IMPACT</button>
                    </div>
                  ) : null}
                </section>
              ))}
            </div>
          </motion.article>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <motion.article variants={motionEnabled ? fadeInUpVariants : undefined} className="border border-[0.5px] bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">KEY COMPETENCIES</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {competencyTags.length ? (
                  competencyTags.map((t) => (
                    <span
                      key={t}
                      className="border border-[0.5px] bg-[#f0f5f2] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]"
                      style={{ borderColor: SURFACE_BORDER }}
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <p className="text-[11px] text-[#6d7a77]">Fit reasons appear here when the job has a score from Discover.</p>
                )}
              </div>
            </motion.article>
            <motion.article variants={motionEnabled ? fadeInUpVariants : undefined} className="border border-[0.5px] bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">TARGET INTERVIEW</p>
              <div className="mt-2 inline-flex items-center gap-2 text-sm text-[#171d1c]">
                <Mi name="business_center" className="text-[13px] text-[#3d4947]" />
                <div>
                  <p className="font-semibold">
                    {company && role ? `${company} · ${role}` : 'No prep session selected'}
                  </p>
                  <p className="text-xs text-[#3d4947]">
                    {selectedSession?.application.job.location?.trim() || 'Location from job record'}
                  </p>
                </div>
              </div>
            </motion.article>
            <motion.article variants={motionEnabled ? fadeInUpVariants : undefined} className="border border-[0.5px] bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">PREPARATION SCORE</p>
              <p className="mt-2 text-[30px] font-semibold leading-none text-[#00685f]">
                {readiness != null ? (
                  <>
                    {readiness.overall}% <span className="text-[11px] uppercase tracking-[0.08em] text-[#3d4947]">HEURISTIC</span>
                  </>
                ) : (
                  <span className="text-[22px] text-[#6d7a77]">—</span>
                )}
              </p>
              <div className="mt-2 h-1 bg-[#eaefed]">
                <div className="h-full bg-[#00685f]" style={{ width: `${readiness?.overall ?? 0}%` }} />
              </div>
              {readiness == null ? (
                <p className="mt-1 text-[10px] text-[#6d7a77]">Scores from prep content length, not employer data.</p>
              ) : null}
            </motion.article>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-12">
            <article className="border border-[0.5px] bg-white dark:bg-slate-900 md:col-span-8" style={{ borderColor: SURFACE_BORDER }}>
              <header className="flex items-center justify-between border-b border-[0.5px] px-3 py-2" style={{ borderColor: SURFACE_BORDER }}>
                <h3 className="text-base font-medium text-[#171d1c]">Recent Peer Feedback</h3>
                <button className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f]">REQUEST NEW</button>
              </header>
              <div className="divide-y divide-[0.5px] px-3" style={{ borderColor: SURFACE_BORDER }}>
                <div className="py-3">
                  <p className="text-xs font-semibold text-[#171d1c]">Prep notes</p>
                  <p className="mt-1 text-xs italic text-[#3d4947]">
                    {selectedSession?.questions[1]?.trim()
                      ? `"${selectedSession.questions[1].trim().slice(0, 280)}${selectedSession.questions[1].length > 280 ? '…' : ''}"`
                      : 'Interview questions from your generated prep pack will show here.'}
                  </p>
                </div>
                <div className="py-3">
                  <p className="text-xs font-semibold text-[#171d1c]">Company brief</p>
                  <p className="mt-1 text-xs italic text-[#3d4947]">
                    {selectedSession?.company_brief?.trim()
                      ? `${selectedSession.company_brief.trim().slice(0, 280)}${selectedSession.company_brief.length > 280 ? '…' : ''}`
                      : 'Run prep generation for this application to pull a brief from your backend.'}
                  </p>
                </div>
              </div>
            </article>
            <motion.article variants={motionEnabled ? fadeInUpVariants : undefined} className="border border-[0.5px] bg-[#1550cc] p-3 text-white md:col-span-4" style={{ borderColor: '#1550cc' }}>
              <div className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.08em]">
                <Mi name="description" className="text-[12px]" />
                LINKED TECH BRIEF
              </div>
              <h3 className="mt-2 text-[22px] font-semibold leading-[1.1] sm:text-[26px]">
                {selectedSession?.application.job.title ?? 'Role briefing'}
              </h3>
              <p className="mt-2 text-[13px] leading-[1.35] text-blue-100">
                {briefExcerpt || 'Company and role context from prep will display here when available.'}
              </p>
              <motion.button {...microInteractionMotion} className="mt-4 inline-flex h-8 w-full items-center justify-center border border-white/40 bg-white dark:bg-slate-900 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#1550cc]">
                OPEN BRIEF WORKSPACE
              </motion.button>
            </motion.article>
          </div>
        </section>

        <aside className="space-y-3 lg:col-span-4">
          <article className="border border-[0.5px] border-l-2 border-l-amber-600 bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-amber-700">Match risks</p>
              <p className="text-[10px] uppercase tracking-[0.08em] text-[#3d4947]">{riskFlags.length} ITEMS</p>
            </div>
            <div className="space-y-2">
              {riskFlags.length ? (
                riskFlags.map((flag) => (
                  <div key={flag} className="border border-[0.5px] bg-[#f8fafc] p-2" style={{ borderColor: SURFACE_BORDER }}>
                    <p className="text-xs font-semibold text-[#171d1c]">Scorer flag</p>
                    <p className="mt-1 text-xs text-[#3d4947]">{flag}</p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-[#3d4947]">No risk flags on this application&apos;s latest score.</p>
              )}
            </div>
          </article>

          <article className="border border-[0.5px] bg-white dark:bg-slate-900" style={{ borderColor: SURFACE_BORDER }}>
            <header className="border-b border-[0.5px] px-3 py-2" style={{ borderColor: SURFACE_BORDER }}>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">STORY LIBRARY</h3>
            </header>
            <div className="divide-y divide-[0.5px]" style={{ borderColor: SURFACE_BORDER }}>
              {lowConfidenceStories.length ? (
                <div className="border-b border-[0.5px] bg-amber-50 px-3 py-2" style={{ borderColor: SURFACE_BORDER }}>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-amber-800">
                    Manual Review Recommended
                  </p>
                  <p className="mt-1 text-xs text-amber-900">
                    {lowConfidenceStories.length} STAR {lowConfidenceStories.length > 1 ? 'stories are' : 'story is'} low confidence.
                    Add specific actions and measurable outcomes before interviews.
                  </p>
                </div>
              ) : null}
              {starStories.length ? (
                starStories.map((story, idx) => {
                  const preview = [story.situation, story.task].join(' ').trim().slice(0, 120)
                  const badge = confidenceBadge(normalizeStoryConfidence(story))
                  return (
                    <div key={`${idx}-${preview.slice(0, 20)}`} className="px-3 py-2">
                      <div className="mb-1 flex items-center justify-between">
                        <p className="text-sm font-medium text-[#171d1c]">STAR story {idx + 1}</p>
                        <div className="inline-flex items-center gap-1.5">
                          <p className={cn('px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em]', badge.className)}>
                            {badge.label}
                          </p>
                          <p className="text-[10px] uppercase tracking-[0.08em] text-[#3d4947]">SAVED</p>
                        </div>
                      </div>
                      <p className="text-xs text-[#3d4947]">{preview || '…'}</p>
                    </div>
                  )
                })
              ) : (
                <p className="px-3 py-4 text-xs text-[#3d4947]">No STAR stories in this prep session yet.</p>
              )}
            </div>
            <button
              type="button"
              className="inline-flex h-9 w-full items-center justify-center border-t border-[0.5px] text-[11px] font-semibold uppercase tracking-[0.08em] text-[#00685f]"
              style={{ borderColor: SURFACE_BORDER }}
            >
              STORIES ({starStories.length})
            </button>
          </article>

          <article className="border border-[0.5px] bg-[#eaefed] p-3" style={{ borderColor: SURFACE_BORDER }}>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">Voice practice</h3>
              <Mi name="mic" className="text-[15px] text-[#00685f]" />
            </div>
            <p className="text-xs text-[#3d4947]">Practice this story with AI Voice Coach.</p>
            <motion.button {...microInteractionMotion} className="mt-3 inline-flex h-8 w-full items-center justify-center gap-1 border border-[0.5px] bg-white dark:bg-slate-900 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#171d1c]" style={{ borderColor: SURFACE_BORDER }}>
              <Mi name="play_circle" className="text-[13px]" />
              START DRILL
            </motion.button>
          </article>
        </aside>
      </div>

      <section className="space-y-4">
        <article
          className="rounded-2xl border border-[0.5px] bg-[#f6fbfa] px-5 py-5 sm:px-6 sm:py-6"
          style={{ borderColor: SURFACE_BORDER }}
        >
          <h3 className="text-[24px] font-medium leading-none tracking-[0.01em] text-[#2f3e3c] sm:text-[32px]">
            TOP TIPS FOR SUCCESS
          </h3>
          <div className="mt-4 space-y-4 sm:mt-5 sm:space-y-5">
            <div className="flex items-start gap-3">
              <ShieldCheck size={18} className="mt-1 shrink-0 text-[#006d66]" />
              <p className="text-[18px] leading-[1.2] text-[#0f1918] sm:text-[22px]">
                <span className="font-semibold">Be Precise.</span> Detailed job titles help our AI filter out noise.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <Zap size={18} className="mt-1 shrink-0 text-[#006d66]" />
              <p className="text-[18px] leading-[1.2] text-[#0f1918] sm:text-[22px]">
                <span className="font-semibold">Stay Active.</span> Checking your progress weekly keeps the algorithm fresh.
              </p>
            </div>
            <div className="flex items-start gap-3">
              <MessageSquareText size={18} className="mt-1 shrink-0 text-[#006d66]" />
              <p className="text-[18px] leading-[1.2] text-[#0f1918] sm:text-[22px]">
                <span className="font-semibold">Ask AI.</span> Use the assistant in the sidebar for resume feedback anytime.
              </p>
            </div>
          </div>
        </article>

        <article
          className="rounded-2xl border border-[0.5px] bg-white px-5 py-5 text-center sm:px-6 sm:py-6"
          style={{ borderColor: SURFACE_BORDER }}
        >
          <p className="text-[14px] font-medium uppercase tracking-[0.08em] text-[#5f6e6c] sm:text-[16px]">Platform Impact</p>
          <p className="mt-2 text-[52px] font-semibold leading-none tracking-[-0.02em] text-[#0058e6] sm:text-[68px]">4.8k+</p>
          <p className="mx-auto mt-2 max-w-3xl text-[18px] leading-[1.24] text-[#2a3433] sm:text-[22px]">
            Professionals placed this month using CareerPath Guides.
          </p>
        </article>

        <article
          className="rounded-2xl border border-[0.5px] bg-white px-5 py-5 sm:px-6 sm:py-6"
          style={{ borderColor: SURFACE_BORDER }}
        >
          <h3 className="text-[36px] font-medium leading-none tracking-[-0.01em] text-[#1a2423] sm:text-[50px]">Stuck?</h3>
          <p className="mt-3 text-[20px] leading-[1.24] text-[#2f3e3c] sm:text-[24px]">
            Our career coaches are available for a 15-min chat.
          </p>
          <motion.button
            {...microInteractionMotion}
            className="mt-5 inline-flex h-12 w-full items-center justify-center rounded-xl border-2 border-[#0058e6] bg-white px-4 text-[18px] font-medium text-[#0058e6] sm:h-14 sm:text-[20px]"
          >
            Schedule Intro Call
          </motion.button>
        </article>

        <article
          className="rounded-2xl border border-[0.5px] bg-[#f2e2ff] px-5 py-4 sm:px-6 sm:py-5"
          style={{ borderColor: '#e0c8ff' }}
        >
          <div className="flex items-center gap-3">
            <div className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-[#e9d4ff] text-[#23005e]">
              <Lightbulb size={20} />
            </div>
            <div>
              <p className="text-[34px] font-medium leading-none tracking-[-0.01em] text-[#23005e] sm:text-[52px]">Did you know?</p>
              <p className="mt-1 text-[18px] leading-[1.2] text-[#23005e] sm:text-[22px]">
                Alex, profiles that include specific industry preferences are 2x more likely to land an interview within the first 30 days.
              </p>
            </div>
          </div>
        </article>
      </section>

    </motion.div>
  )
}
