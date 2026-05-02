import type { AgentState } from '@doubow/shared'

export function AgentStatusCard({ agent }: { agent: AgentState }) {
  return <div className="card p-4 text-sm bg-bg-light-green border border-border-subtle text-primary-green">{agent.label}: {agent.status}</div>
}
