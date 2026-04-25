/**
 * In-memory API stub for local `next dev` when no backend is available.
 * Enable with NEXT_PUBLIC_USE_MOCK_API=true (see .env.example). Disabled in production builds.
 */
import type {
  ActivationKPI,
  AgentName,
  AgentState,
  AgentStatus,
  Application,
  Approval,
  AutopilotRun,
  AutopilotScope,
  Channel,
  DashboardSummary,
  DiscoverJobsResponse,
  IntegrityCheckResult,
  Job,
  JobScore,
  JobSource,
  JobWithScore,
  OnboardingStatus,
  PaginatedResponse,
  ParsedProfile,
  PrepSession,
  ResumeProfile,
  StarStory,
  UserPreferences,
} from '@doubow/shared'

type ChatThreadSummary = {
  id: string
  title: string
  updated_at: string
  created_at: string
}

type ChatThreadMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

type ChatThreadDetail = {
  thread: ChatThreadSummary
  messages: ChatThreadMessage[]
  has_more_messages?: boolean
}

type ChatThreadListResult = {
  threads: ChatThreadSummary[]
  has_more: boolean
}

export class MockHttpError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail)
    this.name = 'MockHttpError'
  }
}

export function isMockApiEnabled(): boolean {
  // `NEXT_PUBLIC_*` is inlined at build time; a prior deploy can keep mock=true in the
  // bundle after Vercel env is cleared. Production must never use in-memory fixtures.
  if (process.env.NODE_ENV === 'production') {
    return false
  }
  if (typeof window !== 'undefined') {
    const w = window as unknown as { __DOUBOW_USE_MOCK_API__?: boolean }
    if (typeof w.__DOUBOW_USE_MOCK_API__ === 'boolean') {
      return w.__DOUBOW_USE_MOCK_API__
    }
  }
  const v = process.env.NEXT_PUBLIC_USE_MOCK_API
  return v === 'true' || v === '1'
}

function randomIdSegment(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID().slice(0, 8)
  }
  return Math.random().toString(36).slice(2, 10)
}

const MOCK_USER_ID = 'user_local_stub'

const COMPANIES = [
  'Riverstone Labs',
  'Blue Harbor Tech',
  'Summit Engineering',
  'Atlas Data Co.',
  'North Peak Systems',
  'Silverline Product',
  'Vertex Applications',
  'Horizon Cloud',
  'Keystone Robotics',
  'Pacific Analytics',
] as const

const COMPANY_DOMAINS = [
  'riverstone.example',
  'blueharbor.example',
  'summit.example',
  'atlasdata.example',
  'northpeak.example',
  'silverline.example',
  'vertex.example',
  'horizon.example',
  'keystone.example',
  'pacific.example',
] as const

const TITLES = [
  'Senior Full-Stack Engineer',
  'Staff Backend Engineer',
  'Product Engineer',
  'ML Platform Engineer',
  'Developer Experience Lead',
  'Security Engineer',
  'Data Infrastructure Engineer',
  'Frontend Architect',
] as const

const LOCATIONS = ['Remote', 'Berlin', 'Amsterdam', 'London', 'Hybrid · NYC', 'Remote · EU'] as const

const SOURCES: JobSource[] = ['ashby', 'greenhouse', 'lever', 'linkedin', 'catalog']

function isoMinutesAgo(min: number): string {
  return new Date(Date.now() - min * 60_000).toISOString()
}

function sourceSiteLabel(source: JobSource): string {
  const labels: Record<JobSource, string> = {
    ashby: 'Ashby',
    greenhouse: 'Greenhouse',
    lever: 'Lever',
    linkedin: 'LinkedIn',
    wellfound: 'Wellfound',
    manual: 'Company site',
    catalog: 'Company site',
  }
  return labels[source]
}

function buildSourceUrl(source: JobSource, domain: string, i: number): string {
  const slug = domain.replace(/\.[^.]+$/, '').replace(/[^a-z0-9-]/gi, '-')
  if (source === 'greenhouse') return `https://boards.greenhouse.io/${slug}/jobs/${9000 + i}`
  if (source === 'lever') return `https://jobs.lever.co/${slug}/${i.toString(16)}`
  if (source === 'ashby') return `https://jobs.ashbyhq.com/${slug}/${i.toString(36)}`
  if (source === 'linkedin') return `https://www.linkedin.com/jobs/view/${1200000 + i}/`
  return `https://${domain}/careers/${slug}-${i}`
}

function makeScore(jobId: string, fit: number): JobScore {
  return {
    job_id: jobId,
    fit_score: Math.min(5, Math.max(1, fit)),
    fit_reasons: ['Stack overlap with your profile', 'Seniority band matches', 'Location / remote fit'],
    risk_flags: fit < 3 ? ['Narrow role title vs your headline'] : [],
    dimension_scores: {
      tech: Math.min(5, fit + 0.2),
      culture: Math.min(5, fit - 0.1),
      seniority: Math.min(5, fit),
      comp: Math.min(5, fit - 0.3),
      location: Math.min(5, fit + 0.15),
    },
    channel_recommendation: 'email',
    scored_at: isoMinutesAgo(5),
  }
}

function makeJob(i: number): JobWithScore {
  const id = `job-mock-${String(i + 1).padStart(4, '0')}`
  const fit = 2.8 + (i % 7) * 0.28
  const source = SOURCES[i % SOURCES.length]
  const domain = COMPANY_DOMAINS[i % COMPANY_DOMAINS.length]
  const job: Job = {
    id,
    source,
    external_id: `ext-${i}`,
    title: `${TITLES[i % TITLES.length]}`,
    company: COMPANIES[i % COMPANIES.length],
    location: LOCATIONS[i % LOCATIONS.length],
    salary_range: i % 3 === 0 ? '€90k – €120k' : '€110k – €145k',
    description: `Excerpt from ${sourceSiteLabel(source)} posting (${domain}): sample listing #${i + 1}. We are building reliable systems for customers who care about quality. You will partner with product and design, ship iteratively, and help raise the bar for engineering craft.`,
    url: buildSourceUrl(source, domain, i),
    posted_at: isoMinutesAgo(60 * 24 + i * 17),
    discovered_at: isoMinutesAgo(200 + i),
    logo_url: undefined,
  }
  return { ...job, score: makeScore(id, fit) }
}

function defaultParsedProfile(): ParsedProfile {
  return {
    name: 'Résumé on file',
    headline: 'Profile fields populated from your uploaded document',
    experience_years: 0,
    skills: [],
    top_skills: [],
    archetypes: [],
    gaps: [],
    summary:
      'Stub API mode: parsed fields are placeholders until you connect a real backend and upload a résumé.',
  }
}

function defaultPreferences(): UserPreferences {
  return {
    target_role: '',
    location: '',
    min_salary: undefined,
    seniority: 'Mid',
    skills: [],
    excluded_companies: [],
  }
}

function makeResume(): ResumeProfile {
  const prefs = defaultPreferences()
  return {
    id: 'resume-mock-1',
    storage_path: '/stub/resume.pdf',
    file_name: 'resume.pdf',
    parsed_profile: defaultParsedProfile(),
    preferences: prefs,
    version: 1,
    created_at: isoMinutesAgo(60 * 24 * 7),
  }
}

function makeStarStory(): StarStory {
  return {
    situation: 'Legacy reporting pipeline missed SLA during a traffic spike.',
    task: 'Stabilize ingestion and add backpressure without over-provisioning.',
    action: 'Introduced queue-based workers, idempotent writes, and observability dashboards.',
    result: 'P99 latency dropped 62%; zero duplicate rows in production.',
    reflection: 'Would add canary deploys earlier next time.',
    tags: ['reliability', 'queues'],
  }
}

function applicationFromJob(job: JobWithScore, status: Application['status'], stage: Application['pipeline_stage']): Application {
  return {
    id: `app-mock-${job.id}`,
    user_id: MOCK_USER_ID,
    job,
    score: job.score,
    status,
    channel: job.score.channel_recommendation,
    last_updated: isoMinutesAgo(30),
    is_stale: false,
    pipeline_stage: stage,
  }
}

function seedApprovals(apps: Application[]): Approval[] {
  const out: Approval[] = []
  const pending = apps[0]
  if (pending) {
    out.push({
      id: 'approval-mock-1',
      application: pending,
      type: 'cover_letter',
      channel: 'email',
      subject: `Application — ${pending.job.title} at ${pending.job.company}`,
      draft_body: `Hi ${pending.job.company} team,\n\nI'm excited about the ${pending.job.title} role.\n\nBest regards`,
      status: 'pending',
      idempotency_key: 'idem-mock-1',
      created_at: isoMinutesAgo(12),
    })
  }
  return out
}

function buildAgentStates(): AgentState[] {
  const defs: { name: AgentName; label: string; description: string }[] = [
    { name: 'discovery', label: 'Discovery', description: 'Surface new roles that fit your profile' },
    { name: 'scorer', label: 'Scoring', description: 'Rank postings for fit and risk' },
    { name: 'tailor', label: 'Tailor', description: 'Align bullets and summaries to each posting' },
    { name: 'writer', label: 'Writer', description: 'Draft outreach with approval gates' },
    { name: 'apply', label: 'Apply', description: 'Hand off to email or ATS flows' },
    { name: 'prep', label: 'Prep', description: 'Interview prep from job context' },
    { name: 'monitor', label: 'Monitor', description: 'Track replies and stage changes' },
    { name: 'orchestrator', label: 'Orchestrator', description: 'Coordinate the workflow' },
  ]
  const statuses: AgentStatus[] = ['idle', 'idle', 'running', 'idle', 'idle', 'idle', 'active', 'idle']
  return defs.map((d, i) => ({
    ...d,
    status: statuses[i] ?? 'idle',
    progress: d.name === 'scorer' ? 0.42 : undefined,
    message: d.name === 'scorer' ? 'Re-scoring batch 2 of 5' : undefined,
    items_processed: d.name === 'discovery' ? 12 : undefined,
    last_run: isoMinutesAgo(8 + i),
  }))
}

// ——— mutable in-memory store (stub API only) ———

let mockJobs: JobWithScore[] = Array.from({ length: 36 }, (_, i) => makeJob(i))
let mockResume = makeResume()
let mockApplications: Application[] = [
  applicationFromJob(mockJobs[0], 'pending', 'approve'),
  applicationFromJob(mockJobs[1], 'saved', 'draft'),
  applicationFromJob(mockJobs[2], 'applied', 'send_prep'),
]
let mockApprovals: Approval[] = seedApprovals(mockApplications)
const idempotencyToAppId = new Map<string, string>()
const prepByAppId = new Map<string, PrepSession>()
let mockAutopilotRuns: AutopilotRun[] = [
  {
    run_id: 'run-mock-1',
    status: 'done',
    scope: 'all',
    replayed: false,
    started_at: isoMinutesAgo(120),
    completed_at: isoMinutesAgo(118),
    item_results: [
      {
        application_id: mockApplications[0]?.id ?? 'app-mock-job-mock-0001',
        status: 'success',
        retryable: false,
        latency_ms: 820,
      },
    ],
  },
]

const threadNow = isoMinutesAgo(2)
const mockChatThreads: ChatThreadListResult = {
  threads: [
    {
      id: 'thread-mock-1',
      title: 'Market scan — saved preferences',
      created_at: isoMinutesAgo(400),
      updated_at: threadNow,
    },
    {
      id: 'thread-mock-2',
      title: 'Interview prep — selected role',
      created_at: isoMinutesAgo(900),
      updated_at: isoMinutesAgo(800),
    },
  ],
  has_more: false,
}

const mockThreadDetails: Record<string, ChatThreadDetail> = {
  'thread-mock-1': {
    thread: mockChatThreads.threads[0],
    messages: [
      {
        id: 'msg-1',
        role: 'assistant',
        content:
          'Here are roles that match the preferences on file. Say which ones you want to dig into first.',
        created_at: isoMinutesAgo(60),
      },
      {
        id: 'msg-2',
        role: 'user',
        content: 'Filter to roles that emphasize payments or regulated industries.',
        created_at: isoMinutesAgo(59),
      },
      {
        id: 'msg-3',
        role: 'assistant',
        content: 'Here are two listings that match that filter in the stub catalog—open each to verify details.',
        created_at: isoMinutesAgo(58),
      },
    ],
    has_more_messages: false,
  },
  'thread-mock-2': {
    thread: mockChatThreads.threads[1],
    messages: [
      {
        id: 'msg-a',
        role: 'assistant',
        content: 'Prep thread: review behavioral questions and company context for your upcoming round.',
        created_at: isoMinutesAgo(120),
      },
    ],
    has_more_messages: false,
  },
}

function parseJsonBody(body: RequestInit['body']): Record<string, unknown> {
  if (body == null || typeof body !== 'string') return {}
  try {
    return JSON.parse(body) as Record<string, unknown>
  } catch {
    return {}
  }
}

function matchApplication(id: string): Application | undefined {
  return mockApplications.find((a) => a.id === id)
}

export async function handleMockRequest<T>(
  path: string,
  init: RequestInit = {},
  extraHeaders: Record<string, string> = {},
): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase()
  const [pathname, queryPart] = path.split('?')
  const qs = new URLSearchParams(queryPart ?? '')

  await Promise.resolve()

  // ——— Dashboard ———
  if (pathname === '/v1/me/dashboard' && method === 'GET') {
    const summary: DashboardSummary = {
      high_fit_count: mockJobs.filter((j) => j.score.fit_score >= 4).length,
      pipeline_count: mockApplications.length,
      pending_approvals: mockApprovals.filter((a) => a.status === 'pending').length,
      evaluated_this_week: Math.min(mockJobs.length, 24),
      avg_fit_score: 3.85,
      applied_awaiting_reply: mockApplications.filter((a) => a.status === 'applied').length,
      total_scored_jobs: mockJobs.length,
      profile_views: 12,
      response_rate_pct: 18,
    }
    return summary as T
  }

  // ——— Jobs ———
  if (pathname === '/v1/jobs' && method === 'GET') {
    const page = Math.max(1, parseInt(qs.get('page') ?? '1', 10) || 1)
    const minFit = parseFloat(qs.get('min_fit') ?? '')
    const location = (qs.get('location') ?? '').trim().toLowerCase()
    let filtered = [...mockJobs]
    if (!Number.isNaN(minFit)) {
      filtered = filtered.filter((j) => j.score.fit_score >= minFit)
    }
    if (location) {
      filtered = filtered.filter((j) => j.location.toLowerCase().includes(location))
    }
    const perPage = 20
    const start = (page - 1) * perPage
    const pageItems = filtered.slice(start, start + perPage)
    const body: PaginatedResponse<JobWithScore> = {
      items: pageItems,
      total: filtered.length,
      page,
      per_page: perPage,
    }
    return body as T
  }

  if (pathname.startsWith('/v1/jobs/') && pathname.endsWith('/dismiss') && method === 'POST') {
    const jobId = pathname.slice('/v1/jobs/'.length, -'/dismiss'.length)
    mockJobs = mockJobs.filter((j) => j.id !== jobId)
    return undefined as T
  }

  if (pathname === '/v1/jobs/discover' && method === 'POST') {
    const payload = parseJsonBody(init.body)
    const jobs = (payload.jobs as { external_id?: string }[] | undefined) ?? []
    const newIds: string[] = []
    for (let i = 0; i < jobs.length; i++) {
      const idx = mockJobs.length + i
      const j = makeJob(idx)
      j.external_id = jobs[i]?.external_id ?? j.external_id
      mockJobs.push(j)
      newIds.push(j.id)
    }
    const res: DiscoverJobsResponse = {
      created: jobs.length,
      updated: 0,
      job_ids: newIds,
    }
    return res as T
  }

  // ——— Applications ———
  if (pathname === '/v1/me/applications' && method === 'GET') {
    const statusFilter = qs.get('status')
    let items = [...mockApplications]
    if (statusFilter) {
      items = items.filter((a) => a.status === statusFilter)
    }
    const body: PaginatedResponse<Application> = {
      items,
      total: items.length,
      page: 1,
      per_page: Math.max(items.length, 1),
    }
    return body as T
  }

  if (pathname === '/v1/me/applications' && method === 'POST') {
    const payload = parseJsonBody(init.body)
    const jobId = String(payload.job_id ?? '')
    const channel = payload.channel as Channel
    const idemKey =
      extraHeaders['Idempotency-Key'] ||
      extraHeaders['idempotency-key'] ||
      undefined

    if (idemKey && idempotencyToAppId.has(idemKey)) {
      const existingId = idempotencyToAppId.get(idemKey)!
      const existing = mockApplications.find((a) => a.id === existingId)
      if (existing) return existing as T
    }

    const job = mockJobs.find((j) => j.id === jobId)
    if (!job) {
      throw new MockHttpError(404, 'Job not found')
    }
    const app: Application = {
      id: `app-mock-${randomIdSegment()}`,
      user_id: MOCK_USER_ID,
      job,
      score: job.score,
      status: 'pending',
      channel: channel || job.score.channel_recommendation,
      last_updated: new Date().toISOString(),
      is_stale: false,
      pipeline_stage: 'draft',
      idempotency_key: idemKey,
    }
    mockApplications.push(app)
    if (idemKey) idempotencyToAppId.set(idemKey, app.id)
    return app as T
  }

  if (pathname.includes('/draft') && pathname.startsWith('/v1/me/applications/') && method === 'POST') {
    const applicationId = pathname.slice('/v1/me/applications/'.length, -'/draft'.length)
    const app = matchApplication(applicationId)
    if (!app) throw new MockHttpError(404, 'Application not found')
    const approval: Approval = {
      id: `approval-mock-${randomIdSegment()}`,
      application: app,
      type: 'cover_letter',
      channel: app.channel,
      subject: `Application — ${app.job.title}`,
      draft_body: `Hello ${app.job.company} team,\n\nI am excited about the ${app.job.title} role.\n\nBest regards`,
      status: 'pending',
      idempotency_key: `draft-${applicationId}`,
      created_at: new Date().toISOString(),
    }
    mockApprovals.push(approval)
    return approval as T
  }

  if (pathname === '/v1/me/applications/integrity-check' && method === 'POST') {
    const result: IntegrityCheckResult = {
      mode: (parseJsonBody(init.body).mode as 'dry_run' | 'apply') ?? 'dry_run',
      summary: { duplicates: 0, stale: 0, status_fixes: 0 },
      changes: [],
    }
    return result as T
  }

  // ——— Autopilot ———
  if (pathname === '/v1/me/autopilot/run' && method === 'POST') {
    const payload = parseJsonBody(init.body)
    const scope = payload.scope as AutopilotScope
    const run: AutopilotRun = {
      run_id: `run-mock-${Date.now()}`,
      status: 'queued',
      scope: scope ?? 'all',
      replayed: false,
      started_at: new Date().toISOString(),
    }
    mockAutopilotRuns = [run, ...mockAutopilotRuns]
    return run as T
  }

  if (pathname.startsWith('/v1/me/autopilot/runs/') && pathname.endsWith('/resume') && method === 'POST') {
    const runId = pathname.slice('/v1/me/autopilot/runs/'.length, -'/resume'.length)
    return { run_id: runId, enqueued: true, detail: null } as T
  }

  if (pathname.startsWith('/v1/me/autopilot/runs/') && method === 'GET') {
    const runId = pathname.slice('/v1/me/autopilot/runs/'.length)
    const run = mockAutopilotRuns.find((r) => r.run_id === runId)
    if (!run) throw new MockHttpError(404, 'Run not found')
    return run as T
  }

  if (pathname === '/v1/me/autopilot/runs' && method === 'GET') {
    const limit = Math.min(100, Math.max(1, parseInt(qs.get('limit') ?? '20', 10) || 20))
    return mockAutopilotRuns.slice(0, limit) as T
  }

  // ——— Approvals ———
  if (pathname === '/v1/me/approvals' && method === 'GET') {
    return [...mockApprovals] as T
  }

  if (pathname.includes('/approve') && pathname.startsWith('/v1/me/approvals/') && method === 'POST') {
    const id = pathname.slice('/v1/me/approvals/'.length, -'/approve'.length)
    const a = mockApprovals.find((x) => x.id === id)
    if (a) {
      a.status = 'approved'
      a.approved_at = new Date().toISOString()
      const now = new Date().toISOString()
      a.sent_at = now
      if (a.channel === 'linkedin') {
        a.send_provider = 'linkedin_email_handoff'
        a.delivery_status = 'provider_accepted'
      } else {
        a.send_provider = 'gmail'
        a.delivery_status = 'provider_confirmed'
      }
    }
    return { approval_id: id, queued_send: false, send_task_id: null } as T
  }

  if (pathname.includes('/reject') && pathname.startsWith('/v1/me/approvals/') && method === 'POST') {
    const id = pathname.slice('/v1/me/approvals/'.length, -'/reject'.length)
    const a = mockApprovals.find((x) => x.id === id)
    if (a) a.status = 'rejected'
    return undefined as T
  }

  // ——— Prep ———
  if (pathname === '/v1/me/prep' && method === 'GET') {
    const applicationId = qs.get('application_id') ?? ''
    if (prepByAppId.has(applicationId)) {
      return prepByAppId.get(applicationId)! as T
    }
    const app = matchApplication(applicationId)
    if (!app) throw new MockHttpError(404, 'Application not found')
    const prep: PrepSession = {
      id: `prep-mock-${applicationId}`,
      application: app,
      questions: [
        'Why this company, why now?',
        'Tell me about a time you improved reliability.',
        'How do you approach trade-offs between speed and quality?',
      ],
      star_stories: [makeStarStory()],
      company_brief: `${app.job.company} builds customer-facing products; confirm details from the live posting before interviews.`,
      created_at: isoMinutesAgo(20),
    }
    prepByAppId.set(applicationId, prep)
    return prep as T
  }

  if (pathname === '/v1/me/prep/generate' && method === 'POST') {
    const applicationId = String(parseJsonBody(init.body).application_id ?? '')
    const app = matchApplication(applicationId)
    if (!app) throw new MockHttpError(404, 'Application not found')
    const prep: PrepSession = {
      id: `prep-mock-${applicationId}`,
      application: app,
      questions: ['Generated Q1 (mock)', 'Generated Q2 (mock)'],
      star_stories: [makeStarStory()],
      company_brief: `Generated brief for ${app.job.company}.`,
      created_at: new Date().toISOString(),
    }
    prepByAppId.set(applicationId, prep)
    return prep as T
  }

  if (pathname === '/v1/me/prep/assist' && method === 'POST') {
    const payload = parseJsonBody(init.body)
    const kind = String(payload.kind ?? 'company_brief')
    return {
      text:
        kind === 'star_story'
          ? 'Practice angle: emphasize measurable outcomes and how you aligned teams under constraints.'
          : 'Research angle: verify the company’s current product focus from primary sources before the interview.',
    } as T
  }

  if (pathname === '/v1/me/prep/capabilities' && method === 'GET') {
    return { assist_route_available: true, llm_configured: true } as T
  }

  // ——— Resume ———
  if (pathname === '/v1/me/resume' && method === 'GET') {
    return mockResume as T
  }

  if (pathname === '/v1/me/onboarding/status' && method === 'GET') {
    const st: OnboardingStatus = {
      state: 'ready',
      current_step: 'first_jobs_ready',
      eta_seconds: null,
      has_resume: true,
      first_jobs_ready: true,
    }
    return st as T
  }

  if (pathname === '/v1/me/resume' && method === 'POST') {
    const body = init.body
    let fileName = 'upload.pdf'
    if (body instanceof FormData) {
      const f = body.get('file')
      if (f instanceof File) fileName = f.name || fileName
    }
    mockResume = {
      ...mockResume,
      file_name: fileName,
      version: mockResume.version + 1,
      parsed_profile: defaultParsedProfile(),
    }
    return mockResume as T
  }

  if (pathname === '/v1/me/preferences' && method === 'PATCH') {
    const patch = parseJsonBody(init.body) as Partial<UserPreferences>
    mockResume = {
      ...mockResume,
      preferences: { ...mockResume.preferences, ...patch },
    }
    return mockResume.preferences as T
  }

  if (pathname === '/v1/me/resume/analyze' && method === 'POST') {
    return {
      analysis:
        'Stub analysis: connect a live LLM backend to generate tailored feedback from your résumé text.',
    } as T
  }

  // ——— Telemetry ———
  if (pathname === '/v1/me/telemetry/events' && method === 'POST') {
    return { status: 'ok' } as T
  }

  if (pathname === '/v1/me/telemetry/activation-kpi' && method === 'GET') {
    const kpi: ActivationKPI = {
      sample_size: 42,
      latest_time_to_first_matches_seconds: 95,
      avg_time_to_first_matches_seconds: 120,
    }
    return kpi as T
  }

  // ——— Debug ———
  if (pathname === '/v1/me/debug' && method === 'GET') {
    return { user_id: MOCK_USER_ID, auth_source: 'clerk_jwt' } as T
  }

  if (pathname === '/v1/me/debug/ai-config' && method === 'GET') {
    return {
      openrouter_configured: false,
      openrouter_api_url: 'https://openrouter.ai/api/v1',
      openrouter_http_referer: null,
      resolved_models: { chat: 'mock', drafts: 'mock' },
    } as T
  }

  // ——— Integrations ———
  if (pathname === '/v1/integrations/google/authorize' && method === 'GET') {
    return { authorization_url: 'https://example.com/mock-google-oauth' } as T
  }
  if (pathname === '/v1/integrations/google/status' && method === 'GET') {
    return { connected: false, google_email: null } as T
  }
  if (pathname === '/v1/integrations/google/' && method === 'DELETE') {
    return { ok: true } as T
  }
  if (pathname === '/v1/integrations/linkedin/authorize' && method === 'GET') {
    return { authorization_url: 'https://example.com/mock-linkedin-oauth' } as T
  }
  if (pathname === '/v1/integrations/linkedin/status' && method === 'GET') {
    return { connected: false, expires_at: null } as T
  }
  if (pathname === '/v1/integrations/linkedin/' && method === 'DELETE') {
    return { ok: true } as T
  }

  // ——— Agents ———
  if (pathname === '/v1/agents/status' && method === 'GET') {
    return buildAgentStates() as T
  }

  if (pathname === '/v1/agents/chat/threads' && method === 'GET') {
    const offset = Math.max(0, parseInt(qs.get('offset') ?? '0', 10) || 0)
    if (offset === 0) return mockChatThreads as T
    return { threads: [], has_more: false } as T
  }

  if (pathname.startsWith('/v1/agents/chat/threads/') && method === 'GET') {
    const rest = pathname.slice('/v1/agents/chat/threads/'.length)
    const threadId = rest.split('?')[0]
    const detail = mockThreadDetails[threadId]
    if (!detail) {
      throw new MockHttpError(404, 'Thread not found')
    }
    return detail as T
  }

  throw new MockHttpError(404, `Stub API: no handler for ${method} ${pathname}`)
}

export function mockAgentStatusSnapshot(): AgentState[] {
  return buildAgentStates()
}
