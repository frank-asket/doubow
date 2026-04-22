'use client'

import { useLayoutEffect } from 'react'
import { useAuth } from '@clerk/nextjs'

import { setAuthTokenGetter } from '@/lib/api'

export default function ClerkApiAuthBridge() {
  const { getToken } = useAuth()

  /** Register before child useEffects run so `/v1/me/*` fetchers receive a Bearer token on first paint. */
  useLayoutEffect(() => {
    setAuthTokenGetter(async () => {
      try {
        return await getToken()
      } catch {
        return null
      }
    })
    return () => setAuthTokenGetter(null)
  }, [getToken])

  return null
}
