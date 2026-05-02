'use client'

import Link from 'next/link'
import { useState } from 'react'
import useSWR from 'swr'
import { Loader2, Sparkles, AlertTriangle, CheckCircle2 } from 'lucide-react'
import {
  ApiError,
  jobSearchPipelineApi,
  mePreferencesApi,
  type FeedbackLearningPreferenceResponse,
  type JobSearchPipelineRunResponse,
} from '../../lib/api'
import { cn } from '../../lib/utils'
import { candidateTokens } from '../../lib/candidateUi'
import { getMicroInteractionMotion, motion, useReducedMotion } from '../../lib/motion'

async function fetchFeedbackLearningSafe() {
  try {
    return await mePreferencesApi.feedbackLearning()
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null
    throw e
  }
}

function hasPersonalizedTuning(data: FeedbackLearningPreferenceResponse | null | undefined): boolean {
  if (!data?.feedback_learning || typeof data.feedback_learning !== 'object') return false
  return Object.keys(data.feedback_learning).length > 0
}

/** Plain-language labels for pipeline stages (avoid internal IDs in customer UI). */
const STAGE_LABELS: Partial<Record<string, string>> = {
  data_collection: 'bringing in new job listings',
  resume_profile: 'updating your profile from your résumé',
  job_matching: 'refreshing job fit scores',
  outbound_application: 'syncing your applications list',
  feedback: 'updating how we learn from your pipeline',
}

function friendlyStageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? stage.replace(/_/g, ' ')
}

function summarizeRun(res: JobSearchPipelineRunResponse): string {
  const failed = res.stages.filter((s) => !s.ok)
  if (failed.length > 0) {
    const parts = failed.map((f) => friendlyStageLabel(f.stage))
    return `We could not finish updating (${parts.join('; ')}). Try again in a moment, or ask Assistant for help.`
  }
  return "You're all set — profile, matches, and applications are up to date."
}

export function MatchPipelineUpdateCard({
  className,
  onAfterRun,
}: {
  className?: string
  onAfterRun?: () => void | Promise<void>
}) {
  const [running, setRunning] = useState(false)
  const [persistLearning, setPersistLearning] = useState(false)
  const [refreshCatalog, setRefreshCatalog] = useState(false)
  const [banner, setBanner] = useState<{ tone: 'ok' | 'err'; text: string } | null>(null)
  const [clearing, setClearing] = useState(false)

  const prefersReducedMotion = useReducedMotion()
  const motionEnabled = !prefersReducedMotion
  const microInteractionMotion = getMicroInteractionMotion(motionEnabled)

  const { data: flData, mutate: mutateFl, error: flError } = useSWR(
    'me-preferences-feedback-learning',
    fetchFeedbackLearningSafe,
    { revalidateOnFocus: false, shouldRetryOnError: false },
  )

  const personalized = hasPersonalizedTuning(flData)

  async function runPipeline() {
    setRunning(true)
    setBanner(null)
    try {
      const res = await jobSearchPipelineApi.run({
        persist_feedback_learning: persistLearning,
        trigger_catalog_refresh: refreshCatalog,
      })
      setBanner({ tone: 'ok', text: summarizeRun(res) })
      await mutateFl()
      await onAfterRun?.()
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.detail || 'Could not complete the update.'
          : 'Could not complete the update.'
      setBanner({ tone: 'err', text: msg })
    } finally {
      setRunning(false)
    }
  }

  async function clearTuning() {
    setClearing(true)
    setBanner(null)
    try {
      await mePreferencesApi.clearFeedbackLearning()
      await mutateFl()
      setBanner({ tone: 'ok', text: 'Role rankings now use the standard mix — not your past activity.' })
      await onAfterRun?.()
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.detail || 'Could not change that setting. Try again.'
          : 'Could not change that setting. Try again.'
      setBanner({ tone: 'err', text: msg })
    } finally {
      setClearing(false)
    }
  }

  return (
    <section
      className={cn(
        'rounded-sm border border-[0.5px] bg-white p-3 dark:bg-slate-900',
        className,
      )}
      style={{ borderColor: 'rgba(109,122,119,0.45)' }}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
            Refresh everything
          </p>
          <p className="text-sm text-zinc-800 dark:text-zinc-100">
            Updates your résumé profile, refreshes how roles are ranked for you, and syncs your applications — the same
            full refresh you can start from Assistant.
          </p>
          {personalized ? (
            <p className="text-xs text-teal-800 dark:text-teal-300">
              Your role rankings reflect how you&apos;ve been applying and responding — not only keywords.
            </p>
          ) : null}
          {flError ? (
            <p className="text-xs text-zinc-500">Could not check personalization settings.</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:items-end">
          <motion.button
            type="button"
            disabled={running}
            onClick={() => void runPipeline()}
            {...microInteractionMotion}
            className="inline-flex items-center justify-center gap-2 rounded-sm border border-[0.5px] px-3 py-2 text-sm font-semibold shadow-sm disabled:opacity-60"
            style={{
              borderColor: candidateTokens.outline,
              background: candidateTokens.surface,
              color: candidateTokens.onSurface,
            }}
          >
            {running ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Sparkles className="h-4 w-4" aria-hidden />
            )}
            {running ? 'Working…' : 'Refresh now'}
          </motion.button>
          <Link
            href="/messages"
            className="text-center text-2xs font-medium text-teal-800 hover:underline dark:text-teal-300 sm:text-right"
          >
            Or ask Assistant to refresh for you
          </Link>
        </div>
      </div>

      <div className="mt-3 flex flex-col gap-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
        <p className="text-2xs font-semibold uppercase tracking-wider text-zinc-400">Optional</p>
        <label className="flex cursor-pointer items-start gap-2 text-xs text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            className="mt-0.5 rounded border-zinc-300"
            checked={persistLearning}
            onChange={(e) => setPersistLearning(e.target.checked)}
          />
          <span>
            <span className="font-medium">Learn from my recent activity</span>
            <span className="block text-zinc-500">
              Improves how we rank jobs based on your applications and pipeline (optional).
            </span>
          </span>
        </label>
        <label className="flex cursor-pointer items-start gap-2 text-xs text-zinc-700 dark:text-zinc-300">
          <input
            type="checkbox"
            className="mt-0.5 rounded border-zinc-300"
            checked={refreshCatalog}
            onChange={(e) => setRefreshCatalog(e.target.checked)}
          />
          <span>
            <span className="font-medium">Also fetch new jobs from the web</span>
            <span className="block text-zinc-500">Takes longer. Use when you want the latest listings from our sources.</span>
          </span>
        </label>
      </div>

      {personalized ? (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
          <motion.button
            type="button"
            disabled={clearing || running}
            onClick={() => void clearTuning()}
            {...microInteractionMotion}
            className="text-2xs font-semibold text-zinc-600 underline-offset-2 hover:underline disabled:opacity-50 dark:text-zinc-400"
          >
            {clearing ? 'Resetting…' : 'Stop personalizing my rankings'}
          </motion.button>
        </div>
      ) : null}

      {banner ? (
        <div
          role="status"
          className={cn(
            'mt-3 flex items-start gap-2 rounded-[10px] border px-3 py-2 text-sm',
            banner.tone === 'ok'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-950'
              : 'border-red-200 bg-red-50 text-red-950',
          )}
        >
          {banner.tone === 'ok' ? (
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" aria-hidden />
          ) : (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-700" aria-hidden />
          )}
          <p className="flex-1">{banner.text}</p>
        </div>
      ) : null}
    </section>
  )
}
