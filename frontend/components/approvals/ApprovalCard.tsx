import type { Approval } from '@/types'

export function ApprovalCard({ approval }: { approval: Approval }) {
  return (
    <div className="card p-4">
      <p className="text-sm font-medium">{approval.application.job.company}</p>
      <p className="text-xs text-surface-500">{approval.type}</p>
    </div>
  )
}
