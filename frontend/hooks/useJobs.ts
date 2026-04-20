import { useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import useSWR from 'swr'

import { isE2EAuthBypass } from '@/lib/e2e'
import { jobsApi } from '@/lib/api'
import { useJobStore } from '@/stores/jobStore'

export function useJobs() {
  const { isLoaded, isSignedIn } = useAuth()
  const { minFit, locationFilter, setJobs, setLoading } = useJobStore()

  const ready = isE2EAuthBypass() || (isLoaded && isSignedIn)
  const { data, error, isLoading, mutate } = useSWR(
    ready ? ['jobs', minFit, locationFilter] : null,
    () => jobsApi.list({ min_fit: minFit || undefined, location: locationFilter || undefined }),
    { revalidateOnFocus: false, dedupingInterval: 30_000 }
  )

  useEffect(() => {
    if (data) setJobs(data.items, data.total)
    setLoading(isLoading)
  }, [data, isLoading, setJobs, setLoading])

  return { error, refresh: mutate }
}
