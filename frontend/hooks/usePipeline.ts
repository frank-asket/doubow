import { useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import useSWR from 'swr'

import { isE2EAuthBypass } from '@/lib/e2e'
import { applicationsApi } from '@/lib/api'
import { usePipelineStore } from '@/stores/pipelineStore'

export function usePipeline(statusFilter?: string) {
  const { isLoaded, isSignedIn } = useAuth()
  const { setApplications, setLoading } = usePipelineStore()

  const ready = isE2EAuthBypass() || (isLoaded && isSignedIn)
  const { data, error, isLoading, mutate } = useSWR(
    ready ? ['applications', statusFilter] : null,
    () => applicationsApi.list(statusFilter),
    { revalidateOnFocus: false }
  )

  useEffect(() => {
    if (data) setApplications(data.items)
    setLoading(isLoading)
  }, [data, isLoading, setApplications, setLoading])

  return { error, refresh: mutate }
}
