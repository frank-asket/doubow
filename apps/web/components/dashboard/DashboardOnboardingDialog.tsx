'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { Route } from 'next'
import type { LucideIcon } from 'lucide-react'
import {
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Compass,
  LayoutDashboard,
  ListFilter,
  Rocket,
  Sparkles,
  Upload,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const STORAGE_PREFIX = 'doubow.dashboard.onboarding.v2'

/** Completed tour — used by Playwright to skip the dialog */
export function dashboardOnboardingStorageKey(userId: string): string {
  return `${STORAGE_PREFIX}:${userId}`
}

/** Pending resume step index after following an in-tour link (session only) */
export function dashboardOnboardingResumeKey(userId: string): string {
  return `${STORAGE_PREFIX}:resume:${userId}`
}

type PrimaryAction = {
  label: string
  href: Route
}

type Step = {
  title: string
  description: string
  icon: LucideIcon
  hints?: string[]
  /** Prominent CTA for this step (e.g. open Resume or Discover) */
  primaryAction?: PrimaryAction
}

/**
 * Full first-run journey: welcome → resume & preferences → discover → pipeline → assistant → finish.
 */
const STEPS: Step[] = [
  {
    title: 'Welcome to your Candidate Hub',
    description:
      'Doubow brings together your resume, job discovery, applications, and interview prep in one workspace. This short tour walks you through the setup that powers everything else.',
    icon: LayoutDashboard,
    hints: [
      'Use the sidebar to switch areas anytime.',
      'Use Next for each step, or follow the teal buttons to jump to a screen — the tour picks up on the next step when you navigate.',
    ],
  },
  {
    title: 'Get first matches',
    description:
      'Upload your resume to unlock first scored matches quickly. Preferences on the same page are optional at first and can be refined after you review early matches.',
    icon: Upload,
    hints: [
      'Resume upload is the only required step for first value.',
      'Use defaults if you are in a hurry; refine role/location/salary after first matches.',
      'Refine skills over time — the Assistant can suggest edits.',
    ],
    primaryAction: { label: 'Open Resume and get matches', href: '/resume' },
  },
  {
    title: 'Explore job matches',
    description:
      'Job matches surfaces roles scored for fit. Review highlights, risks, and channel suggestions before you add anything to your pipeline.',
    icon: Compass,
    hints: [
      'Counts in the sidebar show how many strong matches need attention.',
      'Open a role to see full scoring detail.',
    ],
    primaryAction: { label: 'Browse job matches', href: '/discover' },
  },
  {
    title: 'Pipeline & approvals',
    description:
      'Pipeline tracks every application. When Doubow drafts outreach or follow-ups, Approvals is where you review and send — nothing goes out without you.',
    icon: ListFilter,
    hints: [
      'Move stages as you hear back from employers.',
      'Pending approvals appear in the sidebar badge when something needs you.',
    ],
    primaryAction: { label: 'View Pipeline', href: '/pipeline' },
  },
  {
    title: 'Assistant & interview prep',
    description:
      'Chat with the Assistant for strategy, rewrites, and questions about your search. Use Interviews for role-aware prep and practice.',
    icon: Sparkles,
    hints: [
      'Assistant is available from the sidebar footer.',
      'Prep builds on your profile and active applications.',
    ],
    primaryAction: { label: 'Open Assistant', href: '/messages' },
  },
  {
    title: "You're set — make it yours",
    description:
      'Check Profile settings for Gmail and integrations when you need them. Upgrade from the sidebar when you want higher limits and premium prep. Your overview summarizes momentum at a glance.',
    icon: Rocket,
    hints: [
      'Return to Overview anytime for a snapshot of fits, pipeline, and actions.',
      'Theme toggle lives in the top bar.',
    ],
    primaryAction: { label: 'Go to Overview', href: '/dashboard' },
  },
]

type DashboardOnboardingDialogProps = {
  /** Clerk user id, or `'anon'` when auth is bypassed / disabled */
  onboardingUserId: string | undefined
}

export default function DashboardOnboardingDialog({
  onboardingUserId,
}: DashboardOnboardingDialogProps) {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState(0)
  const initialDelayDone = useRef(false)
  /** Browser timer handle (`number`); avoid `NodeJS.Timeout` from global `setTimeout` typing. */
  const initialDelayTimerRef = useRef<number | null>(null)

  const clearResumeMarker = useCallback(() => {
    if (!onboardingUserId || typeof window === 'undefined') return
    try {
      window.sessionStorage.removeItem(dashboardOnboardingResumeKey(onboardingUserId))
    } catch {
      /* ignore */
    }
  }, [onboardingUserId])

  function persistDismissed() {
    if (!onboardingUserId || typeof window === 'undefined') return
    try {
      window.localStorage.setItem(dashboardOnboardingStorageKey(onboardingUserId), '1')
    } catch {
      /* ignore */
    }
    clearResumeMarker()
  }

  /** First visit: open tour after delay if not completed and not resuming */
  useEffect(() => {
    if (!onboardingUserId || typeof window === 'undefined') return
    try {
      if (window.localStorage.getItem(dashboardOnboardingStorageKey(onboardingUserId))) return
    } catch {
      return
    }
    try {
      if (window.sessionStorage.getItem(dashboardOnboardingResumeKey(onboardingUserId))) return
    } catch {
      /* ignore */
    }
    if (initialDelayDone.current) return
    initialDelayTimerRef.current = window.setTimeout(() => {
      initialDelayDone.current = true
      initialDelayTimerRef.current = null
      setOpen(true)
    }, 450)
    return () => {
      if (initialDelayTimerRef.current) {
        window.clearTimeout(initialDelayTimerRef.current)
        initialDelayTimerRef.current = null
      }
    }
  }, [onboardingUserId])

  /** After navigating away via a primary CTA, reopen at the next step */
  useEffect(() => {
    if (!onboardingUserId || typeof window === 'undefined') return
    try {
      if (window.localStorage.getItem(dashboardOnboardingStorageKey(onboardingUserId))) return
    } catch {
      return
    }

    let raw: string | null = null
    try {
      raw = window.sessionStorage.getItem(dashboardOnboardingResumeKey(onboardingUserId))
    } catch {
      return
    }
    if (raw === null) return

    clearResumeMarker()
    const n = Number.parseInt(raw, 10)
    const clamped =
      Number.isNaN(n) ? 0 : Math.min(Math.max(0, n), STEPS.length - 1)
    if (initialDelayTimerRef.current) {
      window.clearTimeout(initialDelayTimerRef.current)
      initialDelayTimerRef.current = null
    }
    initialDelayDone.current = true
    setStep(clamped)
    const id = window.requestAnimationFrame(() => setOpen(true))
    return () => window.cancelAnimationFrame(id)
  }, [pathname, onboardingUserId, clearResumeMarker])

  function handleOpenChange(next: boolean) {
    if (!next) {
      persistDismissed()
      setStep(0)
    }
    setOpen(next)
  }

  function finish() {
    persistDismissed()
    setOpen(false)
    setStep(0)
  }

  function handlePrimaryActionClick(isLastStep: boolean) {
    if (isLastStep) {
      finish()
      return
    }
    if (!onboardingUserId || typeof window === 'undefined') return
    try {
      const nextIdx = Math.min(step + 1, STEPS.length - 1)
      window.sessionStorage.setItem(
        dashboardOnboardingResumeKey(onboardingUserId),
        String(nextIdx),
      )
    } catch {
      /* ignore */
    }
    setOpen(false)
  }

  const current = STEPS[step]
  const Icon = current.icon
  const last = step === STEPS.length - 1

  return (
    <Dialog.Root open={open} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[100] bg-slate-950/60 backdrop-blur-[2px] data-[state=open]:animate-fade-in" />
        <Dialog.Content
          aria-describedby="onboarding-step-description"
          className={cn(
            'fixed left-[50%] top-[50%] z-[101] max-h-[min(92vh,640px)] w-[min(calc(100vw-2rem),440px)] translate-x-[-50%] translate-y-[-50%]',
            'rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/15 outline-none',
            'dark:border-slate-700 dark:bg-slate-900 dark:shadow-black/40',
            'data-[state=open]:animate-slide-up',
          )}
        >
          <div className="flex max-h-[min(92vh,640px)] flex-col">
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 pb-4 pt-5 dark:border-slate-800">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-500/15 dark:text-teal-300">
                  <Icon size={22} strokeWidth={2} aria-hidden />
                </div>
                <div className="min-w-0">
                  <Dialog.Title className="text-base font-bold leading-snug text-zinc-900 dark:text-white">
                    {current.title}
                  </Dialog.Title>
                  <p className="mt-1 text-[11px] font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
                    Step {step + 1} of {STEPS.length}
                  </p>
                </div>
              </div>
              <Dialog.Close
                type="button"
                className="rounded-lg p-1.5 text-zinc-500 transition-colors hover:bg-slate-100 hover:text-zinc-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                aria-label="Close tour"
              >
                <X size={18} />
              </Dialog.Close>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
              <Dialog.Description id="onboarding-step-description" asChild>
                <p className="text-sm leading-relaxed text-zinc-700 dark:text-slate-300">{current.description}</p>
              </Dialog.Description>

              {current.primaryAction ? (
                <Link
                  href={current.primaryAction.href}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm font-bold text-teal-900 shadow-sm transition-colors hover:bg-teal-100 dark:border-teal-500/40 dark:bg-teal-500/15 dark:text-teal-100 dark:hover:bg-teal-500/25"
                  onClick={() => handlePrimaryActionClick(last)}
                >
                  {current.primaryAction.label}
                  <ChevronRight size={18} aria-hidden />
                </Link>
              ) : null}

              {current.hints && current.hints.length > 0 ? (
                <ul className="mt-4 space-y-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                  {current.hints.map((hint) => (
                    <li
                      key={hint}
                      className="flex gap-2 text-[13px] leading-snug text-zinc-600 dark:text-slate-400"
                    >
                      <CheckSquare className="mt-0.5 h-4 w-4 shrink-0 text-teal-600 dark:text-teal-400" aria-hidden />
                      <span>{hint}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-5 py-4 dark:border-slate-800">
              <div className="flex max-w-[52%] flex-wrap gap-1">
                {STEPS.map((_, i) => (
                  <button
                    key={i}
                    type="button"
                    aria-label={`Go to step ${i + 1}`}
                    aria-current={i === step ? 'step' : undefined}
                    className={cn(
                      'h-1.5 rounded-full transition-all',
                      i === step ? 'w-5 bg-teal-600 dark:bg-teal-400' : 'w-1.5 bg-slate-200 dark:bg-slate-600',
                    )}
                    onClick={() => setStep(i)}
                  />
                ))}
              </div>
              <div className="flex items-center gap-2">
                {step > 0 ? (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-zinc-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                    onClick={() => setStep((s) => Math.max(0, s - 1))}
                  >
                    <ChevronLeft size={16} aria-hidden />
                    Back
                  </button>
                ) : null}
                {last ? (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-lg bg-[#00685f] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:brightness-110"
                    onClick={finish}
                  >
                    Finish tour
                    <ChevronRight size={16} aria-hidden />
                  </button>
                ) : (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-lg bg-[#00685f] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:brightness-110"
                    onClick={() => setStep((s) => s + 1)}
                  >
                    Next
                    <ChevronRight size={16} aria-hidden />
                  </button>
                )}
              </div>
            </div>

            <div className="border-t border-slate-100 bg-slate-50/80 px-5 py-3 dark:border-slate-800 dark:bg-slate-950/50">
              <p className="text-center text-[11px] text-zinc-500 dark:text-slate-500">
                Quick links:{' '}
                <Link href="/resume" className="font-semibold text-teal-700 underline-offset-2 hover:underline dark:text-teal-400">
                  Resume
                </Link>
                {' · '}
                <Link href={'/discover' as Route} className="font-semibold text-teal-700 underline-offset-2 hover:underline dark:text-teal-400">
                  Job matches
                </Link>
                {' · '}
                <Link href={'/messages' as Route} className="font-semibold text-teal-700 underline-offset-2 hover:underline dark:text-teal-400">
                  Assistant
                </Link>
                {' · '}
                <Link href="/settings" className="font-semibold text-teal-700 underline-offset-2 hover:underline dark:text-teal-400">
                  Settings
                </Link>
              </p>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
