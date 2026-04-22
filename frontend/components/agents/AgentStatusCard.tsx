import type { AgentState } from '@doubow/shared'

export function AgentStatusCard({ agent }: { agent: AgentState }) {
  return <div className="card p-4 text-sm">{agent.label}: {agent.status}</div>
}
