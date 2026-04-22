import { telemetryApi } from '@/lib/api'

const ACTIVATION_START_KEY = 'daubo_activation_resume_upload_succeeded_at'

export function trackEvent(
  eventName:
    | 'discover_empty_viewed'
    | 'resume_upload_started'
    | 'resume_upload_succeeded'
    | 'match_scoring_started'
    | 'match_scoring_eta_shown'
    | 'first_matches_ready',
  properties: Record<string, unknown> = {},
): void {
  void telemetryApi.track(eventName, properties, new Date().toISOString()).catch(() => {})
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
