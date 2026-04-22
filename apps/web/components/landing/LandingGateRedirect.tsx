'use client'

import { useAuth } from '@clerk/nextjs'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect } from 'react'

/**
 * Client fallback: middleware sends signed-in users from `/` to `/dashboard`; this catches
 * any client-only edge cases (e.g. hydration) so the marketing page never stays mounted.
 */
export default function LandingGateRedirect() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (pathname !== '/' || !isLoaded || !isSignedIn) return
    router.replace('/dashboard')
  }, [pathname, isLoaded, isSignedIn, router])

  return null
}
