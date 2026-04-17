import { useEffect } from 'react'
import useSWR from 'swr'

import { jobsApi } from '@/lib/api'
import { useJobStore } from '@/stores/jobStore'

export function useJobs() {
  const { minFit, locationFilter, setJobs, setLoading } = useJobStore()

  const { data, error, isLoading, mutate } = useSWR(
    ['jobs', minFit, locationFilter],
    () => jobsApi.list({ min_fit: minFit || undefined, location: locationFilter || undefined }),
    { revalidateOnFocus: false, dedupingInterval: 30_000 }
  )

  useEffect(() => {
    if (data) setJobs(data.items, data.total)
    setLoading(isLoading)
  }, [data, isLoading, setJobs, setLoading])

  return { error, refresh: mutate }
}
