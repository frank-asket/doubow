import { useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import useSWR from 'swr'

import { isE2EAuthBypass } from '@/lib/e2e'
import { applicationsApi } from '@/lib/api'
import { getBrowserSupabaseClient } from '@/lib/supabase'
import { usePipelineStore } from '@/stores/pipelineStore'

export function usePipeline(statusFilter?: string) {
  const { isLoaded, isSignedIn, userId } = useAuth()
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

  useEffect(() => {
    if (!ready || !userId) return
    const supabase = getBrowserSupabaseClient()
    if (!supabase) return

    const channel = supabase
      .channel(`applications-status-${userId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'applications',
          filter: `user_id=eq.${userId}`,
        },
        () => {
          mutate()
        }
      )
      .subscribe()

    return () => {
      void supabase.removeChannel(channel)
    }
  }, [mutate, ready, userId])

  return { error, refresh: mutate }
}
