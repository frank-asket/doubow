import type {
  JobWithScore, DiscoverJobItem, DiscoverJobsResponse, Application, IntegrityCheckResult,
  AutopilotRun, AutopilotScope, Approval, PrepSession,
  AgentState, ResumeProfile, UserPreferences, PaginatedResponse,
  DashboardSummary,
  OnboardingStatus,
  ActivationKPI,
} from '@doubow/shared'

import { handleMockRequest, isMockApiEnabled, mockAgentStatusSnapshot, MockHttpError } from './mock-api'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? '/api'
let authTokenGetter: (() => Promise<string | null>) | null = null

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail)
    this.name = 'ApiError'
  }
}

export function setAuthTokenGetter(getter: (() => Promise<string | null>) | null) {
  authTokenGetter = getter
}

function messageFromErrorBody(body: Record<string, unknown>, fallback: string): string {
  const nested = body.error
  if (nested && typeof nested === 'object' && nested !== null && 'message' in nested) {
    const m = (nested as { message?: unknown }).message
    if (typeof m === 'string') return m
  }
  // Idempotency 409: { error: "idempotency_conflict", detail: "…" }
  if (body.error === 'idempotency_conflict' && typeof body.detail === 'string') {
    return body.detail
  }
  if (typeof body.detail === 'string') return body.detail
  return fallback
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  headers: Record<string, string> = {},
): Promise<T> {
  const token = authTokenGetter ? await authTokenGetter() : null
  const mergedHeaders = new Headers(init.headers ?? {})
  if (!(init.body instanceof FormData) && !mergedHeaders.has('Content-Type')) {
    mergedHeaders.set('Content-Type', 'application/json')
  }
  if (token) {
    mergedHeaders.set('Authorization', `Bearer ${token}`)
  }
  for (const [key, value] of Object.entries(headers)) {
    mergedHeaders.set(key, value)
  }

  if (isMockApiEnabled()) {
    try {
      const headerRecord: Record<string, string> = {}
      mergedHeaders.forEach((value, key) => {
        headerRecord[key] = value
      })
      return await handleMockRequest<T>(path, init, headerRecord)
    } catch (e) {
      if (e instanceof MockHttpError) throw new ApiError(e.status, e.detail)
      throw e
    }
  }

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: mergedHeaders,
    credentials: 'include',
  })
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as Record<string, unknown>
    throw new ApiError(res.status, messageFromErrorBody(body, res.statusText))
  }
  if (res.status === 204) {
    return undefined as T
  }
  const text = await res.text()
  if (!text.trim()) {
    return undefined as T
  }
  return JSON.parse(text) as T
}

// ─── Dashboard ─────────────────────────────────────────────────────────────

export const dashboardApi = {
  get: () => request<DashboardSummary>('/v1/me/dashboard'),
}

// ─── Jobs ──────────────────────────────────────────────────────────────────

export const jobsApi = {
  list: (params: { min_fit?: number; location?: string; page?: number } = {}) => {
    const q = new URLSearchParams()
    if (params.min_fit)   q.set('min_fit', String(params.min_fit))
    if (params.location)  q.set('location', params.location)
    if (params.page)      q.set('page', String(params.page))
    return request<PaginatedResponse<JobWithScore>>(`/v1/jobs?${q}`)
  },
  dismiss: (jobId: string) =>
    request<void>(`/v1/jobs/${jobId}/dismiss`, { method: 'POST' }),
  discover: (jobs: DiscoverJobItem[]) =>
    request<DiscoverJobsResponse>('/v1/jobs/discover', {
      method: 'POST',
      body: JSON.stringify({ jobs }),
    }),
}

// ─── Applications ──────────────────────────────────────────────────────────

export const applicationsApi = {
  list: (status?: string) => {
    const q = status ? `?status=${status}` : ''
    return request<PaginatedResponse<Application>>(`/v1/me/applications${q}`)
  },
  create: (jobId: string, channel: string, opts?: { idempotencyKey?: string }) =>
    request<Application>(
      '/v1/me/applications',
      {
        method: 'POST',
        body: JSON.stringify({ job_id: jobId, channel }),
      },
      opts?.idempotencyKey ? { 'Idempotency-Key': opts.idempotencyKey } : {},
    ),
  integrityCheck: (mode: 'dry_run' | 'apply') =>
    request<IntegrityCheckResult>('/v1/me/applications/integrity-check', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  createDraft: (applicationId: string) =>
    request<Approval>(`/v1/me/applications/${encodeURIComponent(applicationId)}/draft`, {
      method: 'POST',
    }),
}

// ─── Autopilot ─────────────────────────────────────────────────────────────

export const autopilotApi = {
  run: (
    scope: AutopilotScope,
    applicationIds: string[] | null,
    idempotencyKey: string,
  ) =>
    request<AutopilotRun>(
      '/v1/me/autopilot/run',
      {
        method: 'POST',
        body: JSON.stringify({ scope, application_ids: applicationIds }),
      },
      { 'Idempotency-Key': idempotencyKey },
    ),
  getRun: (runId: string) =>
    request<AutopilotRun>(`/v1/me/autopilot/runs/${runId}`),
  listRuns: (limit: number = 20) =>
    request<AutopilotRun[]>(`/v1/me/autopilot/runs?limit=${Math.max(1, Math.min(100, limit))}`),
  /** Re-enqueue a stuck ``running`` run that has a LangGraph checkpoint (after worker loss). */
  resumeRun: (runId: string) =>
    request<{ run_id: string; enqueued: boolean; detail?: string | null }>(
      `/v1/me/autopilot/runs/${encodeURIComponent(runId)}/resume`,
      { method: 'POST' },
    ),
}

// ─── Approvals ─────────────────────────────────────────────────────────────

export const approvalsApi = {
  list: () => request<Approval[]>('/v1/me/approvals'),
  approve: (id: string, editedBody?: string) =>
    request<{ approval_id: string; queued_send: boolean; send_task_id?: string | null }>(
      `/v1/me/approvals/${id}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({ edited_body: editedBody ?? null }),
      },
      // Backend requires Idempotency-Key for approve-once semantics.
      {
        'Idempotency-Key':
          typeof crypto !== 'undefined' && 'randomUUID' in crypto
            ? `approve_${id}_${crypto.randomUUID()}`
            : `approve_${id}_${Date.now()}_${Math.random().toString(36).slice(2, 14)}`,
      },
    ),
  reject: (id: string) =>
    request<void>(`/v1/me/approvals/${id}/reject`, { method: 'POST' }),
}

// ─── Prep ──────────────────────────────────────────────────────────────────

export const prepApi = {
  getForApplication: (applicationId: string) =>
    request<PrepSession>(`/v1/me/prep?application_id=${applicationId}`),
  generate: (applicationId: string) =>
    request<PrepSession>('/v1/me/prep/generate', {
      method: 'POST',
      body: JSON.stringify({ application_id: applicationId }),
    }),
  assist: (applicationId: string, kind: 'company_brief' | 'star_story') =>
    request<{ text: string }>('/v1/me/prep/assist', {
      method: 'POST',
      body: JSON.stringify({ application_id: applicationId, kind }),
    }),
  /** Capability probe that avoids validation-error noise in DevTools. */
  checkAssistCapability: async (): Promise<{ available: boolean; llmConfigured: boolean }> => {
    const res = await request<{ assist_route_available: boolean; llm_configured: boolean }>(
      '/v1/me/prep/capabilities',
    )
    return {
      available: Boolean(res.assist_route_available),
      llmConfigured: Boolean(res.llm_configured),
    }
  },
}

// ─── Resume ────────────────────────────────────────────────────────────────

export const resumeApi = {
  get: () => request<ResumeProfile>('/v1/me/resume'),
  onboardingStatus: () => request<OnboardingStatus>('/v1/me/onboarding/status'),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<ResumeProfile>('/v1/me/resume', {
      method: 'POST',
      body: form,
      headers: {},
    })
  },
  updatePreferences: (prefs: Partial<UserPreferences>) =>
    request<UserPreferences>('/v1/me/preferences', {
      method: 'PATCH',
      body: JSON.stringify(prefs),
    }),
  analyzeProfile: () =>
    request<{ analysis: string }>('/v1/me/resume/analyze', { method: 'POST' }),
}

// ─── Telemetry ──────────────────────────────────────────────────────────────

type TelemetryEventName =
  | 'discover_empty_viewed'
  | 'resume_upload_started'
  | 'resume_upload_succeeded'
  | 'match_scoring_started'
  | 'match_scoring_eta_shown'
  | 'first_matches_ready'

export const telemetryApi = {
  track: (event_name: TelemetryEventName, properties: Record<string, unknown> = {}, occurred_at?: string) =>
    request<{ status: 'ok' }>('/v1/me/telemetry/events', {
      method: 'POST',
      body: JSON.stringify({ event_name, properties, occurred_at: occurred_at ?? null }),
    }),
  activationKpi: () => request<ActivationKPI>('/v1/me/telemetry/activation-kpi'),
}

// ─── Auth debug ─────────────────────────────────────────────────────────────

export const authApi = {
  meDebug: () => request<{ user_id: string; auth_source: 'clerk_jwt' }>('/v1/me/debug'),
  aiConfig: () =>
    request<{
      openrouter_configured: boolean
      openrouter_api_url: string
      openrouter_http_referer: string | null
      resolved_models: Record<string, string>
    }>('/v1/me/debug/ai-config'),
}

// ─── Google / Gmail (OAuth link for approval sends) ────────────────────────

export const googleIntegrationsApi = {
  getAuthorizationUrl: () =>
    request<{ authorization_url: string }>('/v1/integrations/google/authorize'),
  status: () =>
    request<{ connected: boolean; google_email: string | null }>('/v1/integrations/google/status'),
  disconnect: () =>
    request<{ ok: boolean }>('/v1/integrations/google/', { method: 'DELETE' }),
}

// ─── LinkedIn (OAuth link for note handoff) ─────────────────────────────────

export const linkedinIntegrationsApi = {
  getAuthorizationUrl: () =>
    request<{ authorization_url: string }>('/v1/integrations/linkedin/authorize'),
  status: () =>
    request<{ connected: boolean; expires_at: string | null }>('/v1/integrations/linkedin/status'),
  disconnect: () =>
    request<{ ok: boolean }>('/v1/integrations/linkedin/', { method: 'DELETE' }),
}

// ─── Agents ────────────────────────────────────────────────────────────────

export const agentsApi = {
  status: () => request<AgentState[]>('/v1/agents/status'),
}

export type ChatThreadSummary = {
  id: string
  title: string
  updated_at: string
  created_at: string
}

export type ChatThreadMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export type ChatThreadDetail = {
  thread: ChatThreadSummary
  messages: ChatThreadMessage[]
  has_more_messages?: boolean
}

export type ChatThreadListResult = {
  threads: ChatThreadSummary[]
  has_more: boolean
}

export const agentChatApi = {
  listThreads: (limit: number = 20, offset: number = 0) =>
    request<ChatThreadListResult>(
      `/v1/agents/chat/threads?limit=${Math.max(1, Math.min(100, limit))}&offset=${Math.max(0, offset)}`,
    ),
  getThread: (
    threadId: string,
    opts?: { limit?: number; beforeMessageId?: string },
  ) => {
    const q = new URLSearchParams()
    if (opts?.limit) q.set('limit', String(opts.limit))
    if (opts?.beforeMessageId) q.set('before_message_id', opts.beforeMessageId)
    const qs = q.toString()
    return request<ChatThreadDetail>(
      `/v1/agents/chat/threads/${encodeURIComponent(threadId)}${qs ? `?${qs}` : ''}`,
    )
  },
}

// ─── SSE streams ───────────────────────────────────────────────────────────

/** SSE with Clerk Bearer token — native EventSource cannot set Authorization headers. */
export function streamAgentStatus(
  onEvent: (event: AgentState) => void,
  onError?: (err: Event) => void,
): () => void {
  if (isMockApiEnabled()) {
    if (typeof window === 'undefined') {
      return () => {}
    }
    const states = mockAgentStatusSnapshot()
    states.forEach((s, idx) => {
      window.setTimeout(() => onEvent(s), 40 * idx)
    })
    let i = 0
    const id = window.setInterval(() => {
      onEvent(states[i % states.length])
      i += 1
    }, 2800)
    return () => clearInterval(id)
  }

  const controller = new AbortController()
  ;(async () => {
    const token = authTokenGetter ? await authTokenGetter() : null
    const headers = new Headers({ Accept: 'text/event-stream' })
    if (token) headers.set('Authorization', `Bearer ${token}`)
    try {
      const res = await fetch(`${BASE}/v1/agents/status/stream`, {
        credentials: 'include',
        headers,
        signal: controller.signal,
      })
      if (!res.ok) {
        onError?.(new Event('error'))
        return
      }
      const reader = res.body?.getReader()
      if (!reader) {
        onError?.(new Event('error'))
        return
      }
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() ?? ''
        for (const block of chunks) {
          for (const line of block.split('\n')) {
            const trimmed = line.trimStart()
            if (!trimmed.startsWith('data:')) continue
            const payload = trimmed.slice(5).trim()
            if (!payload || payload === '[DONE]') continue
            try {
              onEvent(JSON.parse(payload) as AgentState)
            } catch {
              /* ignore malformed chunk */
            }
          }
        }
      }
    } catch {
      if (!controller.signal.aborted) onError?.(new Event('error'))
    }
  })()
  return () => controller.abort()
}

export function streamOrchestratorChat(
  message: string,
  onChunk: (text: string) => void,
  options?: { threadId?: string | null; onMeta?: (meta: { thread_id?: string }) => void },
  onDone?: () => void,
  onError?: (err: string) => void,
): () => void {
  if (isMockApiEnabled()) {
    if (typeof window === 'undefined') {
      return () => {}
    }
    let aborted = false
    const reply = `Assistant (stub API): you said “${message.slice(0, 120)}${message.length > 120 ? '…' : ''}”. Connect a live chat backend for model replies; this response is generated locally.`
    const parts = reply.split(/(\s+)/)
    let idx = 0
    queueMicrotask(() => {
      options?.onMeta?.({ thread_id: options?.threadId ?? 'thread-mock-1' })
    })
    const step = () => {
      if (aborted) return
      if (idx < parts.length) {
        onChunk(parts[idx])
        idx += 1
        window.setTimeout(step, 22)
      } else {
        onDone?.()
      }
    }
    window.setTimeout(step, 0)
    return () => {
      aborted = true
    }
  }

  let aborted = false
  const controller = new AbortController()

  ;(async () => {
    const token = authTokenGetter ? await authTokenGetter() : null
    const headers = new Headers({ 'Content-Type': 'application/json' })
    if (token) headers.set('Authorization', `Bearer ${token}`)

    return fetch(`${BASE}/v1/agents/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, thread_id: options?.threadId ?? null }),
      credentials: 'include',
      signal: controller.signal,
    })
  })().then(async (res) => {
    if (!res.ok) {
      if (res.status === 404) {
        onError?.(
          'Agents chat API not found (404). Restart the backend from backend/api_gateway so POST /v1/agents/chat is loaded, ' +
            'or confirm NEXT_PUBLIC_API_URL matches the gateway you run locally.',
        )
      } else if (res.status === 401) {
        onError?.('Sign in required to use orchestrator chat.')
      } else {
        onError?.(`Request failed (${res.status}).`)
      }
      return
    }
    const reader = res.body?.getReader()
    if (!reader) return
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      if (aborted) break
      const { done, value } = await reader.read()
      if (done) { onDone?.(); break }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data:')) continue
        const data = line.slice(5).trim()
        if (data === '[DONE]') { onDone?.(); return }
        try {
          const parsed = JSON.parse(data)
          if (parsed.meta && typeof parsed.meta === 'object') {
            options?.onMeta?.(parsed.meta as { thread_id?: string })
            continue
          }
          if (parsed.delta?.text) onChunk(parsed.delta.text)
        } catch {}
      }
    }
  }).catch((err) => {
    if (!aborted) onError?.(err.message)
  })

  return () => { aborted = true; controller.abort() }
}
