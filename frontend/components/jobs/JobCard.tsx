import type { JobWithScore } from '@/types'

export function JobCard({ job }: { job: JobWithScore }) {
  return <div className="card p-4">{job.title}</div>
}
