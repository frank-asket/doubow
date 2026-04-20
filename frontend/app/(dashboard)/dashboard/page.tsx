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
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-surface-800">Dashboard walkthrough</h1>
        <p className="text-sm text-surface-500 mt-0.5">
          Full interactive overview of every panel. Click any section to explore its purpose and product decisions.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-5">
        {PANEL_DETAILS.map((panel) => {
          const Icon = panel.icon
          const isActive = panel.key === selected
          return (
            <div
              key={panel.key}
              className={cn(
                'card p-4 transition-all duration-150 border',
                isActive
                  ? 'border-brand-200 bg-brand-50 shadow-card'
                  : 'border-surface-200 hover:border-surface-300 hover:bg-surface-50'
              )}
            >
              <button
                onClick={() => setSelected(panel.key)}
                className="w-full text-left"
              >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="w-8 h-8 rounded-md bg-white border border-surface-200 flex items-center justify-center">
                  <Icon size={15} className={isActive ? 'text-brand-600' : 'text-surface-500'} />
                </div>
                <span className="text-2xs px-2 py-0.5 rounded-full bg-surface-100 text-surface-500">
                  {panel.badge}
                </span>
              </div>
              <p className="text-sm font-medium text-surface-800">{panel.title}</p>
              <p className="text-xs text-surface-500 mt-1 line-clamp-2">{panel.subtitle}</p>
              </button>
              <Link
                href={panel.href}
                className="inline-flex items-center gap-1 mt-3 text-xs text-brand-700 font-medium hover:text-brand-800"
              >
                Go to panel <ChevronRight size={12} />
              </Link>
            </div>
          )
        })}
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-brand-50 border border-brand-100 flex items-center justify-center">
              <ActiveIcon size={15} className="text-brand-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-surface-800">{active.title}</p>
              <p className="text-xs text-surface-500">{active.subtitle}</p>
            </div>
          </div>
          <span className="text-2xs px-2 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-100">
            Panel rationale
          </span>
        </div>

        <div className="space-y-2.5">
          {active.decisions.map((decision) => (
            <div key={decision} className="flex items-start gap-2.5">
              <ChevronRight size={13} className="text-brand-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-surface-700 leading-relaxed">{decision}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 pt-4 border-t border-surface-100 flex items-start gap-2.5">
          <Sparkles size={14} className="text-brand-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1 flex items-center justify-between gap-3">
            <p className="text-xs text-surface-500">
              This overview mirrors how your existing pages are intended to behave so stakeholders can understand
              interaction design and safety decisions before full backend workflows are enabled.
            </p>
            <Link href={active.href} className="btn btn-primary text-xs whitespace-nowrap">
              Go to panel
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
