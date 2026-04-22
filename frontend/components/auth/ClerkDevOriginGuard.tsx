'use client'

import { useEffect } from 'react'

/**
 * In development, mismatched browser origin vs NEXT_PUBLIC_APP_URL breaks Clerk cookies
 * and redirects (localhost vs 127.0.0.1, wrong port). OAuth / redirects can surface as
 * "Unsafe attempt to load URL … from frame … chrome-error://chromewebdata/" when the real
 * issue is a failed navigation or disconnected dev server — check the Network tab first.
 */
export default function ClerkDevOriginGuard() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return

    const expectedRaw = process.env.NEXT_PUBLIC_APP_URL?.trim()
    if (!expectedRaw) return

    let expected: URL
    try {
      expected = new URL(expectedRaw)
    } catch {
      console.warn('[Doubow] NEXT_PUBLIC_APP_URL is not a valid absolute URL.')
      return
    }

    const actual = window.location.origin
    if (expected.origin !== actual) {
      console.warn(
        `[Doubow] Origin mismatch: page is ${actual} but NEXT_PUBLIC_APP_URL is ${expected.origin}. ` +
          'Use the same host in the address bar as in .env (pick either localhost or 127.0.0.1) and mirror that in Clerk Dashboard → Paths / authorized URLs. ',
      )
    }
  }, [])

  return null
}
