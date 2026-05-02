import type { Approval } from '@doubow/shared'

export function ApprovalCard({ approval }: { approval: Approval }) {
  return (
    <div className="card p-4 bg-bg-light-green border border-border-subtle">
      <p className="text-sm font-medium text-primary-green">{approval.application.job.company}</p>
      <p className="text-xs text-text-muted">{approval.type}</p>
    </div>
  )
}
