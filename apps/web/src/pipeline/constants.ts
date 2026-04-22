import type { ApplicationStatus, IntegrityChangeType } from '@doubow/shared'

export const PIPELINE_STATUS_TABS: { label: string; value: ApplicationStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Applied', value: 'applied' },
  { label: 'Interview', value: 'interview' },
  { label: 'Pending', value: 'pending' },
  { label: 'Rejected', value: 'rejected' },
]

export const INTEGRITY_CHANGE_LABELS: Record<IntegrityChangeType, string> = {
  deduplicate: '⊕ Deduplicate',
  mark_stale: '⏱ Mark stale',
  normalize_status: '↻ Normalize status',
}

export const PIPELINE_TABLE_HEADERS = ['Company', 'Role', 'Fit', 'Channel', 'Status', 'Last update', ''] as const
