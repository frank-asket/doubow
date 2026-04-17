import { create } from 'zustand'

import type { Application, IntegrityCheckResult } from '@/types'

interface PipelineStore {
  applications: Application[]
  loading: boolean
  integrityResult: IntegrityCheckResult | null
  integrityLoading: boolean
  setApplications: (apps: Application[]) => void
  setLoading: (v: boolean) => void
  setIntegrityResult: (r: IntegrityCheckResult | null) => void
  setIntegrityLoading: (v: boolean) => void
  updateStatus: (id: string, status: Application['status']) => void
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  applications: [],
  loading: false,
  integrityResult: null,
  integrityLoading: false,
  setApplications: (applications) => set({ applications }),
  setLoading: (loading) => set({ loading }),
  setIntegrityResult: (integrityResult) => set({ integrityResult }),
  setIntegrityLoading: (integrityLoading) => set({ integrityLoading }),
  updateStatus: (id, status) =>
    set((s) => ({
      applications: s.applications.map((a) => (a.id === id ? { ...a, status } : a)),
    })),
}))
