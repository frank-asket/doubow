import { create } from 'zustand'

import type { Approval } from '@/types'

interface ApprovalStore {
  approvals: Approval[]
  loading: boolean
  setApprovals: (a: Approval[]) => void
  setLoading: (v: boolean) => void
  removeApproval: (id: string) => void
  updateApproval: (id: string, patch: Partial<Approval>) => void
}

export const useApprovalStore = create<ApprovalStore>((set) => ({
  approvals: [],
  loading: false,
  setApprovals: (approvals) => set({ approvals }),
  setLoading: (loading) => set({ loading }),
  removeApproval: (id) => set((s) => ({ approvals: s.approvals.filter((a) => a.id !== id) })),
  updateApproval: (id, patch) =>
    set((s) => ({
      approvals: s.approvals.map((a) => (a.id === id ? { ...a, ...patch } : a)),
    })),
}))
