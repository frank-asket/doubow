import { useEffect } from 'react'
import useSWR from 'swr'

import { applicationsApi } from '@/lib/api'
import { usePipelineStore } from '@/stores/pipelineStore'

export function usePipeline(statusFilter?: string) {
  const { setApplications, setLoading } = usePipelineStore()

  const { data, error, isLoading, mutate } = useSWR(
    ['applications', statusFilter],
    () => applicationsApi.list(statusFilter),
    { revalidateOnFocus: false }
  )

  useEffect(() => {
    if (data) setApplications(data.items)
    setLoading(isLoading)
  }, [data, isLoading, setApplications, setLoading])

  return { error, refresh: mutate }
}
