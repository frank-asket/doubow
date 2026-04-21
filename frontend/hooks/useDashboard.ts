import { useAuth } from '@clerk/nextjs'
import useSWR from 'swr'

import { isE2EAuthBypass } from '@/lib/e2e'
import { dashboardApi } from '@/lib/api'

export function useDashboard() {
  const { isLoaded, isSignedIn } = useAuth()
  const ready = isE2EAuthBypass() || (isLoaded && isSignedIn)

  const { data, error, isLoading, mutate } = useSWR(
    ready ? 'dashboard' : null,
    () => dashboardApi.get(),
    {
      revalidateOnFocus: true,
      dedupingInterval: 15_000,
      shouldRetryOnError: false,
      errorRetryCount: 0,
    }
  )

  return {
    summary: data,
    loading: isLoading,
    error,
    refresh: mutate,
  }
}
