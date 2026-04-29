'use client'

import posthog from 'posthog-js'
import { telemetryApi } from '@/lib/api'

const ACTIVATION_START_KEY = 'daubo_activation_resume_upload_succeeded_at'

function capturePostHogMirror(
  eventName: string,
  properties: Record<string, unknown>,
): void {
  if (!process.env.NEXT_PUBLIC_POSTHOG_KEY || typeof window === 'undefined') return
  try {
    posthog.capture(eventName, properties)
  } catch {
    /* non-fatal: backend track remains source of truth */
  }
}

export function trackEvent(
  eventName:
    | 'discover_empty_viewed'
    | 'resume_upload_started'
    | 'resume_upload_succeeded'
    | 'match_scoring_started'
    | 'match_scoring_eta_shown'
    | 'first_matches_ready'
    | 'pricing_interval_toggled'
    | 'pricing_cta_clicked'
    | 'pricing_billing_link_clicked'
    | 'onboarding_step_clicked'
    | 'onboarding_skip_clicked'
    | 'settings_reconnect_clicked'
    | 'settings_contact_support_clicked'
    | 'billing_checkout_returned',
  properties: Record<string, unknown> = {},
): void {
  void telemetryApi.track(eventName, properties, new Date().toISOString()).catch(() => {})
  capturePostHogMirror(eventName, properties)
}

export function setActivationStartNow(): void {
  try {
    localStorage.setItem(ACTIVATION_START_KEY, new Date().toISOString())
  } catch {}
}

export function getActivationStartAt(): string | null {
  try {
    return localStorage.getItem(ACTIVATION_START_KEY)
  } catch {
    return null
  }
}

export function clearActivationStart(): void {
  try {
    localStorage.removeItem(ACTIVATION_START_KEY)
  } catch {}
}
