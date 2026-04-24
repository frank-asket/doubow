export const APP_NAME = 'Doubow'

export const ROUTES = {
  discover: '/discover',
  pipeline: '/pipeline',
  approvals: '/approvals',
  prep: '/prep',
  resume: '/resume',
  /** Unified Assistant (chat); `/agents` redirects here */
  assistant: '/messages',
  /** @deprecated Use `assistant`; kept for deep links — `/agents` redirects to `/messages` */
  agents: '/messages',
  designReference: '/design-reference',
} as const
