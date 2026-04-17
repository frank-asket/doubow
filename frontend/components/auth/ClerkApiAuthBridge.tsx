'use client'

import { useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'

import { setAuthTokenGetter } from '@/lib/api'

export default function ClerkApiAuthBridge() {
  const { getToken, isSignedIn } = useAuth()

  useEffect(() => {
    setAuthTokenGetter(async () => {
      if (!isSignedIn) return null
      return getToken()
    })
    return () => setAuthTokenGetter(null)
  }, [getToken, isSignedIn])

  return null
}
