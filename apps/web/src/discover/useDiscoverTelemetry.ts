'use client'

import { useEffect, useRef } from 'react'
import type { OnboardingStatus } from '@doubow/shared'
import { clearActivationStart, getActivationStartAt, trackEvent } from '../../lib/telemetry'

export function useDiscoverTelemetry({
  onboarding,
  jobsLength,
  refreshJobs,
}: {
  onboarding: OnboardingStatus | undefined
  jobsLength: number
  refreshJobs: () => Promise<unknown>
}) {
  const emptyTracked = useRef(false)
  const scoringTracked = useRef(false)
  const etaTracked = useRef(false)
  const readyTracked = useRef(false)

  useEffect(() => {
    if (onboarding?.state === 'ready' && jobsLength === 0) {
      void refreshJobs()
    }
  }, [onboarding?.state, jobsLength, refreshJobs])

  useEffect(() => {
    if (onboarding?.state === 'no_resume' && !emptyTracked.current) {
      trackEvent('discover_empty_viewed')
      emptyTracked.current = true
      return
    }
    if (onboarding?.state !== 'no_resume') {
      emptyTracked.current = false
    }
  }, [onboarding?.state])

  useEffect(() => {
    if (onboarding?.state === 'scoring_in_progress' && !scoringTracked.current) {
      trackEvent('match_scoring_started', { step: onboarding.current_step })
      scoringTracked.current = true
      return
    }
    if (onboarding?.state !== 'scoring_in_progress') {
      scoringTracked.current = false
    }
  }, [onboarding?.state, onboarding?.current_step])

  useEffect(() => {
    if (onboarding?.state === 'scoring_in_progress' && onboarding.eta_seconds != null && !etaTracked.current) {
      trackEvent('match_scoring_eta_shown', { eta_seconds: onboarding.eta_seconds })
      etaTracked.current = true
      return
    }
    if (onboarding?.state !== 'scoring_in_progress') {
      etaTracked.current = false
    }
  }, [onboarding?.state, onboarding?.eta_seconds])

  useEffect(() => {
    if (onboarding?.state === 'ready' && !readyTracked.current) {
      const startedAt = getActivationStartAt()
      const nowIso = new Date().toISOString()
      let timeToFirstMatchesSeconds: number | null = null
      if (startedAt) {
        const delta = (Date.parse(nowIso) - Date.parse(startedAt)) / 1000
        if (Number.isFinite(delta) && delta >= 0) {
          timeToFirstMatchesSeconds = delta
        }
      }
      trackEvent('first_matches_ready', {
        time_to_first_matches_seconds: timeToFirstMatchesSeconds,
        first_jobs_count: jobsLength,
      })
      clearActivationStart()
      readyTracked.current = true
      return
    }
    if (onboarding?.state !== 'ready') {
      readyTracked.current = false
    }
  }, [onboarding?.state, jobsLength])
}
