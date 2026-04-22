import type { Application } from '@doubow/shared'

export function hasPipelineIntegrityIssues(applications: Application[]): boolean {
  return applications.some((application) => application.is_stale || application.dedup_group)
}
