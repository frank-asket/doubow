'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import type { Route } from 'next'
import {
  Compass,
  ListFilter,
  CheckSquare,
  BookOpen,
  FileText,
  Cpu,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'

type PanelKey = 'discover' | 'pipeline' | 'approvals' | 'prep' | 'resume' | 'agents'

type PanelDetail = {
  key: PanelKey
  title: string
  subtitle: string
  icon: React.ElementType
  badge: string
  href: Route
  decisions: string[]
}

const PANEL_DETAILS: PanelDetail[] = [
  {
    key: 'discover',
    title: 'Discover',
    subtitle: 'Start point for surfaced jobs and fit scoring',
    icon: Compass,
    badge: '12 high-fit',
    href: '/discover',
    decisions: [
      'Discovery scans portals while Scorer rates jobs against your resume profile before they appear here.',
      'Top stat cards show search health at a glance (evaluated jobs, high-fit opportunities, average fit, applied count).',
      'Job cards are collapsed by default to keep scan speed high and avoid overload.',
      'Expand a card to inspect five-dimension scoring, fit reasons, and explicit risk flags.',
      'Prepare application queues writing work only; it does not send anything.',
    ],
  },
  {
    key: 'pipeline',
    title: 'Pipeline',
    subtitle: 'Dense application tracker optimized for fast scanning',
    icon: ListFilter,
    badge: 'status tabs',
    href: '/pipeline',
    decisions: [
      'Status tabs let you segment quickly when managing 7 to 50 concurrent applications.',
      'Integrity banner appears when Monitor detects stale rows, duplicates, or state drift.',
      'Dry-run preview is shown before applying cleanup so users stay in control.',
      'Table is intentionally compact and data-dense for operational decision-making.',
      'Refresh and integrity actions keep the canonical application state trustworthy.',
    ],
  },
  {
    key: 'approvals',
    title: 'Approvals',
    subtitle: 'Human-in-the-loop gate before any outbound action',
    icon: CheckSquare,
    badge: 'critical control',
    href: '/approvals',
    decisions: [
      'Every Writer draft lands here in pending state with channel, subject, and body preview.',
      'Users can edit inline before approving to preserve human voice and intent.',
      'Nothing sends until Approve & send is pressed.',
      'Apply agent verifies approved state as its first operation and hard-stops otherwise.',
      'This panel is the main safety rail for automation trust.',
    ],
  },
  {
    key: 'prep',
    title: 'Interview Prep',
    subtitle: 'Per-application prep, not generic interview advice',
    icon: BookOpen,
    badge: 'JD + resume',
    href: '/prep',
    decisions: [
      'Prep generation is tied to a specific application, job description, and your resume.',
      'Question sets focus on likely interview pressure points for that exact role.',
      'STAR-R scaffold reduces blank-page anxiety with concrete narrative structure.',
      'Stories are designed around your real work and measurable outcomes.',
      'Company brief and role context help prioritize what to practice first.',
    ],
  },
  {
    key: 'resume',
    title: 'Resume',
    subtitle: 'Source of truth shared across all agents',
    icon: FileText,
    badge: 'system context',
    href: '/resume',
    decisions: [
      'Resume profile powers scoring, tailoring, writing quality, and prep relevance.',
      'Scorer uses extracted skills and archetypes for fit ranking.',
      'Tailor grounds modifications in your actual background to prevent skill fabrication.',
      'Writer uses headline and summary to keep output consistent with your profile.',
      'Analysis highlights archetypes and skill gaps to guide role prioritization.',
    ],
  },
  {
    key: 'agents',
    title: 'Agents',
    subtitle: 'Operational visibility and orchestration context',
    icon: Cpu,
    badge: 'live state',
    href: '/agents',
    decisions: [
      'Agent roster shows what is active, idle, or running in the background.',
      'Apply agent staying idle is intentional until an approval event occurs.',
      'Orchestrator chat accepts natural language questions over full pipeline context.',
      'Queries like low-score diagnosis and focus prioritization are answered with project-specific context.',
      'Transparency improves user trust in autonomous workflows.',
    ],
  },
]

export default function DashboardOverviewPage() {
  const [selected, setSelected] = useState<PanelKey>('discover')

  const active = useMemo(
    () => PANEL_DETAILS.find((item) => item.key === selected) ?? PANEL_DETAILS[0],
    [selected]
  )
  const ActiveIcon = active.icon

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      <section className="rounded-3xl border border-emerald-500/20 bg-gradient-to-b from-emerald-500/10 via-zinc-950 to-black p-5 sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Dashboard walkthrough</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400 sm:text-base">
          Full interactive overview of every panel. Click any section to explore its purpose and product decisions.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
        {PANEL_DETAILS.map((panel) => {
          const Icon = panel.icon
          const isActive = panel.key === selected
          return (
            <div
              key={panel.key}
              className={cn(
                'rounded-2xl border bg-[#080808] p-3.5 transition-all duration-150',
                isActive
                  ? 'border-emerald-500/30 bg-emerald-500/10'
                  : 'border-zinc-800 hover:border-zinc-700 hover:bg-zinc-950'
              )}
            >
              <button
                onClick={() => setSelected(panel.key)}
                className="w-full text-left"
              >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-800 bg-zinc-950">
                  <Icon size={15} className={isActive ? 'text-emerald-300' : 'text-zinc-400'} />
                </div>
                <span className="rounded-full bg-zinc-900 px-2 py-0.5 text-2xs text-zinc-400">
                  {panel.badge}
                </span>
              </div>
              <p className="text-sm font-medium text-zinc-100">{panel.title}</p>
              <p className="mt-1 line-clamp-2 text-xs text-zinc-400">{panel.subtitle}</p>
              </button>
              <Link
                href={panel.href}
                className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-emerald-300 hover:text-emerald-200"
              >
                Go to panel <ChevronRight size={12} />
              </Link>
            </div>
          )
        })}
      </div>

      <div className="rounded-3xl border border-zinc-800 bg-[#080808] p-4 sm:p-5">
        <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md border border-emerald-500/20 bg-emerald-500/10">
              <ActiveIcon size={15} className="text-emerald-300" />
            </div>
            <div>
              <p className="text-sm font-semibold text-zinc-100">{active.title}</p>
              <p className="text-xs text-zinc-400">{active.subtitle}</p>
            </div>
          </div>
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-2xs text-emerald-300">
            Panel rationale
          </span>
        </div>

        <div className="space-y-2.5">
          {active.decisions.map((decision) => (
            <div key={decision} className="flex items-start gap-2.5">
              <ChevronRight size={13} className="mt-0.5 flex-shrink-0 text-emerald-300" />
              <p className="text-sm leading-relaxed text-zinc-300">{decision}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 flex items-start gap-2.5 border-t border-zinc-800 pt-4">
          <Sparkles size={14} className="mt-0.5 flex-shrink-0 text-emerald-300" />
          <div className="flex flex-1 flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <p className="text-xs text-zinc-400">
              This overview mirrors how your existing pages are intended to behave so stakeholders can understand
              interaction design and safety decisions before full backend workflows are enabled.
            </p>
            <Link href={active.href} className="btn btn-primary self-start whitespace-nowrap text-xs sm:self-auto">
              Go to panel
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
