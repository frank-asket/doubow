import type { JobWithScore } from '@doubow/shared'

export function JobCard({ job }: { job: JobWithScore }) {
  return <div className="card p-4 bg-bg-light-green border border-border-subtle text-primary-green font-semibold">{job.title}</div>
}
