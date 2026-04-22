import type { JobWithScore } from '@doubow/shared'

export function JobCard({ job }: { job: JobWithScore }) {
  return <div className="card p-4">{job.title}</div>
}
