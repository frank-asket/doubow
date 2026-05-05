'use client'

import Link from 'next/link'
import { Globe, ShieldCheck, Timer } from 'lucide-react'
import type { ReactNode } from 'react'
import type { JobWithScore, OnboardingStatus } from '@doubow/shared'
import { AnimatePresence, fadeInUpVariants, motion, staggerContainerVariants } from '../../lib/motion'
import { cn } from '../../lib/utils'
import { AnimatedMetricValue } from './discoverShared'

const ONBOARDING_STEP_LABELS: Record<string, string> = {
  upload_complete: 'Upload complete',
  parsing_resume: 'Parsing resume',
  scoring_job_matches: 'Scoring job matches',
  building_first_queue: 'Building your first queue',
  first_jobs_ready: 'First jobs ready',
}

export function DiscoverJobsList({
  loading,
  jobsLength,
  filteredJobs,
  jobsForList,
  onboarding,
  etaMinutes,
  motionEnabled,
  onResetFilters,
  renderJobCard,
  renderJobSkeleton,
}: {
  loading: boolean
  jobsLength: number
  filteredJobs: JobWithScore[]
  jobsForList: JobWithScore[]
  onboarding: OnboardingStatus | undefined
  etaMinutes: number | null
  motionEnabled: boolean
  onResetFilters: () => void
  renderJobCard: (job: JobWithScore) => ReactNode
  renderJobSkeleton: (idx: number) => ReactNode
}) {
  const onboardingSteps = [
    'upload_complete',
    'parsing_resume',
    'scoring_job_matches',
    'building_first_queue',
  ] as const
  const showFeaturedCard = jobsForList.length !== filteredJobs.length

  return (
    <>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Top matches · <AnimatedMetricValue className="mx-1" value={String(jobsForList.length)} /> in list
          {showFeaturedCard ? ' · spotlight above' : ''}
        </p>
      </div>

      <div className="space-y-3">
        <AnimatePresence initial={false} mode="popLayout">
          {loading ? (
            <motion.div
              key="loading"
              variants={motionEnabled ? fadeInUpVariants : undefined}
              initial={motionEnabled ? 'hidden' : false}
              animate={motionEnabled ? 'visible' : undefined}
              exit={motionEnabled ? 'exit' : undefined}
              className="space-y-3"
            >
              {Array.from({ length: 4 }).map((_, i) => renderJobSkeleton(i))}
            </motion.div>
          ) : filteredJobs.length === 0 && onboarding?.state === 'no_resume' ? (
            <motion.div
              key="empty-no-resume"
              variants={motionEnabled ? fadeInUpVariants : undefined}
              initial={motionEnabled ? 'hidden' : false}
              animate={motionEnabled ? 'visible' : undefined}
              exit={motionEnabled ? 'exit' : undefined}
              className="card p-4 sm:p-4 text-zinc-600"
            >
              <div className="mx-auto max-w-2xl text-center">
                <div className="mb-3 inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-2xs font-medium text-amber-900">
                  No resume connected
                </div>
                <p className="text-lg font-medium text-zinc-900">Start with a resume upload to unlock your first scored matches.</p>
                <p className="mt-2 text-sm text-zinc-500">
                  Upload first for immediate scoring, then refine preferences later if needed.
                </p>
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                  <Link href="/resume" className="btn btn-primary text-xs">Upload Resume</Link>
                  <Link href="/resume" className="text-xs font-medium text-zinc-600 underline-offset-2 hover:underline">
                    Learn how matching works
                  </Link>
                </div>
              </div>
            </motion.div>
          ) : filteredJobs.length === 0 && onboarding?.state === 'scoring_in_progress' ? (
            <motion.div
              key="empty-scoring"
              variants={motionEnabled ? fadeInUpVariants : undefined}
              initial={motionEnabled ? 'hidden' : false}
              animate={motionEnabled ? 'visible' : undefined}
              exit={motionEnabled ? 'exit' : undefined}
              className="card p-4 sm:p-4"
            >
              <div className="mx-auto max-w-2xl">
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-secondary-green/30 bg-bg-light-green px-2 py-0.5 text-2xs font-medium text-primary-green">
                    Scoring in progress
                  </span>
                  {etaMinutes != null && (
                    <span className="rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-2xs text-zinc-700">
                      <Timer size={10} className="inline" /> ~{etaMinutes} min
                    </span>
                  )}
                </div>
                <p className="text-lg font-medium text-zinc-900">Great — your resume is uploaded.</p>
                <p className="mt-1 text-sm text-zinc-500">
                  We are scoring your first set of jobs now. This usually takes about 1 to 2 minutes.
                </p>
                <div className="mt-5 space-y-2">
                  {onboardingSteps.map((step) => {
                    const active = onboarding.current_step === step
                    const done = onboardingSteps.indexOf(onboarding.current_step as typeof onboardingSteps[number]) > onboardingSteps.indexOf(step)
                    return (
                      <div
                        key={step}
                        className="flex items-center justify-between rounded-sm border border-[#e7e8ee] bg-zinc-50 px-3 py-2"
                      >
                        <span className={cn('text-xs', active ? 'text-zinc-900' : 'text-zinc-500')}>
                          {ONBOARDING_STEP_LABELS[step]}
                        </span>
                        <span className={cn('text-2xs', done ? 'text-emerald-700' : active ? 'text-primary-green' : 'text-zinc-400')}>
                          {done ? 'Done' : active ? 'In progress' : 'Pending'}
                        </span>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 flex items-start gap-2 rounded-sm border border-secondary-green/20 bg-bg-light-green/90 p-3 text-xs text-primary-green">
                  <ShieldCheck size={13} className="mt-0.5 shrink-0 text-primary-green" />
                  You can leave this page. We keep processing in the background.
                </div>
              </div>
            </motion.div>
          ) : filteredJobs.length === 0 && jobsLength > 0 ? (
            <motion.div
              key="empty-filtered"
              variants={motionEnabled ? fadeInUpVariants : undefined}
              initial={motionEnabled ? 'hidden' : false}
              animate={motionEnabled ? 'visible' : undefined}
              exit={motionEnabled ? 'exit' : undefined}
              className="card p-4 sm:p-4 text-center text-zinc-600"
            >
              <Globe size={28} className="mx-auto mb-3 text-zinc-300" />
              <p className="text-sm font-medium text-zinc-800">Nothing matches right now</p>
              <p className="mt-1 text-xs text-zinc-500">
                Try a different search, lower the min fit score, or clear the location filter.
              </p>
              <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  className="btn text-xs"
                  onClick={onResetFilters}
                >
                  Reset search & filters
                </button>
              </div>
            </motion.div>
          ) : filteredJobs.length === 0 ? (
            <motion.div
              key="empty-default"
              variants={motionEnabled ? fadeInUpVariants : undefined}
              initial={motionEnabled ? 'hidden' : false}
              animate={motionEnabled ? 'visible' : undefined}
              exit={motionEnabled ? 'exit' : undefined}
              className="py-16 text-center text-zinc-500"
            >
              <Globe size={28} className="mx-auto mb-3 text-zinc-300" />
              <p className="text-sm font-medium text-zinc-800">No matches yet</p>
              <p className="mt-1 text-xs text-zinc-500">Upload your resume and click Refresh to discover roles</p>
            </motion.div>
          ) : (
            <motion.div
              key="job-list"
              variants={motionEnabled ? staggerContainerVariants : undefined}
              initial={motionEnabled ? 'hidden' : false}
              animate={motionEnabled ? 'visible' : undefined}
              exit={motionEnabled ? 'exit' : undefined}
              className="space-y-3"
            >
              <AnimatePresence initial={false} mode="popLayout">
                {jobsForList.map((job) => renderJobCard(job))}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}
