import { useEffect } from 'react'
import useSWR from 'swr'

import { approvalsApi } from '../../../../frontend/lib/api'
import { useApprovalStore } from './approvalStore'

export function useApprovals() {
  const { setApprovals, setLoading } = useApprovalStore()

  const { data, error, isLoading, mutate } = useSWR('approvals', () => approvalsApi.list(), {
    revalidateOnFocus: true,
    refreshInterval: 15_000,
  })

  useEffect(() => {
    if (data) setApprovals(data)
    setLoading(isLoading)
  }, [data, isLoading, setApprovals, setLoading])

  return { error, refresh: mutate }
}
