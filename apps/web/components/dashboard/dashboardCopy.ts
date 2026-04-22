import type { ApplicationStatus } from '@doubow/shared'

export function formatApplicationStatus(status: ApplicationStatus): string {
  const map: Record<ApplicationStatus, string> = {
    saved: 'Saved',
    pending: 'Pending',
    applied: 'Applied',
    interview: 'Interview',
    offer: 'Offer',
    rejected: 'Rejected',
  }
  return map[status] ?? status
}
