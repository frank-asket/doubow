'use client'

import { useMemo, useState } from 'react'
import { cn } from '../../lib/utils'
import type { PrepSession } from '@doubow/shared'
import { usePrepSessions } from './usePrepSessions'

const SURFACE_BORDER = 'rgba(109,122,119,0.38)'

function Mi({
  name,
  className,
}: {
  name: string
  className?: string
}) {
  return <span className={cn('material-symbols-outlined leading-none', className)}>{name}</span>
}

function deriveReadiness(session: PrepSession | null): { overall: number; technical: number; cultural: number } {
  if (!session) {
    return {
      overall: 84,
      technical: 88,
      cultural: 72,
    }
  }
  const storyCount = session.star_stories.length
  const questionCount = session.questions.length
  const technical = Math.max(45, Math.min(95, 62 + questionCount * 6))
  const cultural = Math.max(42, Math.min(92, 54 + storyCount * 9))
  const overall = Math.round((technical + cultural) / 2)
  return { overall, technical, cultural }
}

export default function PrepPage() {
  const [situation, setSituation] = useState('')
  const [task, setTask] = useState('')
  const [action, setAction] = useState('')
  const [result, setResult] = useState('')
  const [reflection, setReflection] = useState('')
  const { selectedSession } = usePrepSessions()

  const readiness = useMemo(() => deriveReadiness(selectedSession), [selectedSession])
  const company = selectedSession?.application.job.company ?? 'Google'
  const role = selectedSession?.application.job.title ?? 'L6'
  const focusQuestion =
    selectedSession?.questions[0]?.replace(/^["']|["']$/g, '') ??
    'What exact steps did you take? Focus on "I" not "We".'

  return (
    <div className="mx-auto max-w-[1140px] space-y-3 px-3 py-3 sm:px-4">
      <section className="border-b border-[0.5px] pb-2" style={{ borderColor: SURFACE_BORDER }}>
        <div className="mb-1 text-[10px] uppercase tracking-[0.08em] text-[#6c7774]">WORKSPACES / STAR-R BUILDER</div>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-[36px] font-medium leading-[1.05] tracking-[-0.012em] text-[#171d1c]">Interview Preparation Hub</h1>
            <p className="mt-1 text-[13px] text-[#3d4947]">Structured behavioral answer construction and technical briefing tool.</p>
          </div>
          <div className="inline-flex items-center gap-2">
            <button className="inline-flex h-8 items-center border border-[0.5px] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#171d1c]" style={{ borderColor: SURFACE_BORDER }}>
              EXPORT BRIEF
            </button>
            <button className="inline-flex h-8 items-center gap-1 border border-[0.5px] border-[#008378] bg-[#00685f] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-white">
              <Mi name="add" className="text-[12px]" />
              NEW STORY
            </button>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <section className="space-y-4 lg:col-span-8">
          <article className="border border-[0.5px] bg-white dark:bg-slate-900" style={{ borderColor: SURFACE_BORDER }}>
            <header className="flex items-center justify-between border-b border-[0.5px] bg-[#eaefed] px-3 py-1.5" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#3d4947]">ACTIVE DRAFT: PROJECT FALCON SYSTEM MIGRATION</p>
              <span className="bg-teal-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-teal-800">SAVED TO CLOUD</span>
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
          </article>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <article className="border border-[0.5px] bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">KEY COMPETENCIES</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {['LEADERSHIP', 'TECHNICAL DEPTH', 'CONFLICT RES'].map((t) => (
                  <span key={t} className="border border-[0.5px] bg-[#f0f5f2] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]" style={{ borderColor: SURFACE_BORDER }}>
                    {t}
                  </span>
                ))}
              </div>
            </article>
            <article className="border border-[0.5px] bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">TARGET INTERVIEW</p>
              <div className="mt-2 inline-flex items-center gap-2 text-sm text-[#171d1c]">
                <Mi name="business_center" className="text-[13px] text-[#3d4947]" />
                <div>
                  <p className="font-semibold">{company} {role}</p>
                  <p className="text-xs text-[#3d4947]">System Design</p>
                </div>
              </div>
            </article>
            <article className="border border-[0.5px] bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">PREPARATION SCORE</p>
              <p className="mt-2 text-[30px] font-semibold leading-none text-[#00685f]">{readiness.overall}% <span className="text-[11px] uppercase tracking-[0.08em] text-[#3d4947]">READY</span></p>
              <div className="mt-2 h-1 bg-[#eaefed]">
                <div className="h-full bg-[#00685f]" style={{ width: `${readiness.overall}%` }} />
              </div>
            </article>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-12">
            <article className="border border-[0.5px] bg-white dark:bg-slate-900 md:col-span-8" style={{ borderColor: SURFACE_BORDER }}>
              <header className="flex items-center justify-between border-b border-[0.5px] px-3 py-2" style={{ borderColor: SURFACE_BORDER }}>
                <h3 className="text-base font-medium text-[#171d1c]">Recent Peer Feedback</h3>
                <button className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f]">REQUEST NEW</button>
              </header>
              <div className="divide-y divide-[0.5px] px-3" style={{ borderColor: SURFACE_BORDER }}>
                <div className="py-3">
                  <p className="text-xs font-semibold text-[#171d1c]">Alex Chen (Senior Staff Eng)</p>
                  <p className="mt-1 text-xs italic text-[#3d4947]">"The SITUATION is strong, but the ACTION needs more emphasis on how you personally navigated stakeholder resistance."</p>
                </div>
                <div className="py-3">
                  <p className="text-xs font-semibold text-[#171d1c]">Sarah Miller (Tech Recruiter)</p>
                  <p className="mt-1 text-xs italic text-[#3d4947]">"Excellent quantification in RESULT. This story maps perfectly to leadership principles."</p>
                </div>
              </div>
            </article>
            <article className="border border-[0.5px] bg-[#1550cc] p-3 text-white md:col-span-4" style={{ borderColor: '#1550cc' }}>
              <div className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.08em]">
                <Mi name="description" className="text-[12px]" />
                LINKED TECH BRIEF
              </div>
              <h3 className="mt-2 text-[30px] font-semibold leading-[1.02]">Distributed Systems Resilience</h3>
              <p className="mt-2 text-[13px] leading-[1.35] text-blue-100">Brief covers circuit breakers, exponential backoff, and sharding strategies related to this story.</p>
              <button className="mt-4 inline-flex h-8 w-full items-center justify-center border border-white/40 bg-white dark:bg-slate-900 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#1550cc]">
                OPEN BRIEF WORKSPACE
              </button>
            </article>
          </div>
        </section>

        <aside className="space-y-3 lg:col-span-4">
          <article className="border border-[0.5px] border-l-2 border-l-amber-600 bg-white dark:bg-slate-900 p-3" style={{ borderColor: SURFACE_BORDER }}>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-amber-700">NEEDS REVIEW</p>
              <p className="text-[10px] uppercase tracking-[0.08em] text-[#3d4947]">2 ITEMS</p>
            </div>
            <div className="space-y-2">
              <div className="border border-[0.5px] bg-[#f8fafc] p-2" style={{ borderColor: SURFACE_BORDER }}>
                <p className="text-xs font-semibold text-[#171d1c]">Vague Action Verbs</p>
                <p className="mt-1 text-xs text-[#3d4947]">You used "helped with" three times. AI suggests "orchestrated" or "architected".</p>
                <button className="mt-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f]">FIX ALL</button>
              </div>
              <div className="border border-[0.5px] bg-[#f8fafc] p-2" style={{ borderColor: SURFACE_BORDER }}>
                <p className="text-xs font-semibold text-[#171d1c]">Missing Metrics</p>
                <p className="mt-1 text-xs text-[#3d4947]">Result section lacks quantifiable data. Did efficiency increase? By how much?</p>
              </div>
            </div>
          </article>

          <article className="border border-[0.5px] bg-white dark:bg-slate-900" style={{ borderColor: SURFACE_BORDER }}>
            <header className="border-b border-[0.5px] px-3 py-2" style={{ borderColor: SURFACE_BORDER }}>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">STORY LIBRARY</h3>
            </header>
            <div className="divide-y divide-[0.5px]" style={{ borderColor: SURFACE_BORDER }}>
              {[
                ['Falcon Migration', 'Technical leadership during high-traffic outage.', 'ACTIVE'],
                ['Conflict with PM', 'Navigating scope creep during Q3 roadmap.', 'COMPLETE'],
                ['Mentoring Junior Eng', 'Onboarding and growth framework implementation.', 'DRAFT'],
              ].map(([title, desc, status]) => (
                <div key={title} className="px-3 py-2">
                  <div className="mb-1 flex items-center justify-between">
                    <p className="text-sm font-medium text-[#171d1c]">{title}</p>
                    <p className="text-[10px] uppercase tracking-[0.08em] text-[#3d4947]">{status}</p>
                  </div>
                  <p className="text-xs text-[#3d4947]">{desc}</p>
                </div>
              ))}
            </div>
            <button className="inline-flex h-9 w-full items-center justify-center border-t border-[0.5px] text-[11px] font-semibold uppercase tracking-[0.08em] text-[#00685f]" style={{ borderColor: SURFACE_BORDER }}>
              VIEW ALL STORIES (12)
            </button>
          </article>

          <article className="border border-[0.5px] bg-[#eaefed] p-3" style={{ borderColor: SURFACE_BORDER }}>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#3d4947]">MOCK SIMULATOR</h3>
              <Mi name="mic" className="text-[15px] text-[#00685f]" />
            </div>
            <p className="text-xs text-[#3d4947]">Practice this story with AI Voice Coach.</p>
            <button className="mt-3 inline-flex h-8 w-full items-center justify-center gap-1 border border-[0.5px] bg-white dark:bg-slate-900 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#171d1c]" style={{ borderColor: SURFACE_BORDER }}>
              <Mi name="play_circle" className="text-[13px]" />
              START DRILL
            </button>
          </article>
        </aside>
      </div>

    </div>
  )
}
