import { create } from 'zustand'

import type { JobWithScore } from '@doubow/shared'

interface JobStore {
  jobs: JobWithScore[]
  total: number
  loading: boolean
  minFit: number
  locationFilter: string
  hasSalaryOnly: boolean
  setJobs: (jobs: JobWithScore[], total: number) => void
  setLoading: (v: boolean) => void
  setMinFit: (v: number) => void
  setLocationFilter: (v: string) => void
  setHasSalaryOnly: (v: boolean) => void
  dismissJob: (id: string) => void
}

export const useJobStore = create<JobStore>((set) => ({
  jobs: [],
  total: 0,
  loading: false,
  minFit: 0,
  locationFilter: '',
  hasSalaryOnly: false,
  setJobs: (jobs, total) => set({ jobs, total }),
  setLoading: (loading) => set({ loading }),
  setMinFit: (minFit) => set({ minFit }),
  setLocationFilter: (locationFilter) => set({ locationFilter }),
  setHasSalaryOnly: (hasSalaryOnly) => set({ hasSalaryOnly }),
  dismissJob: (id) => set((s) => ({ jobs: s.jobs.filter((j) => j.id !== id) })),
}))
