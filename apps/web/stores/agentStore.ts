import { create } from 'zustand'

import type { AgentName, AgentState, AutopilotRun } from '@/types'

interface AgentStore {
  agents: AgentState[]
  currentRun: AutopilotRun | null
  setAgents: (a: AgentState[]) => void
  updateAgent: (name: AgentName, patch: Partial<AgentState>) => void
  setCurrentRun: (r: AutopilotRun | null) => void
}

export const useAgentStore = create<AgentStore>((set) => ({
  agents: [],
  currentRun: null,
  setAgents: (agents) => set({ agents }),
  updateAgent: (name, patch) =>
    set((s) => ({
      agents: s.agents.map((a) => (a.name === name ? { ...a, ...patch } : a)),
    })),
  setCurrentRun: (currentRun) => set({ currentRun }),
}))
