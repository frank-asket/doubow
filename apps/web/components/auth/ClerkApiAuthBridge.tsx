'use client'

import { useEffect, useLayoutEffect } from 'react'
import posthog from 'posthog-js'
import { useAuth, useUser } from '@clerk/nextjs'

import { setAuthTokenGetter } from '@/lib/api'

export default function ClerkApiAuthBridge() {
  const { getToken } = useAuth()
  const { isSignedIn, user } = useUser()

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

  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_POSTHOG_KEY) return
    if (isSignedIn && user?.id) {
      posthog.identify(user.id)
    }
  }, [isSignedIn, user?.id])

  return null
}
