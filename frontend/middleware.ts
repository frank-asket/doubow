import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

const isProtectedRoute = createRouteMatcher([
  '/discover(.*)',
  '/pipeline(.*)',
  '/approvals(.*)',
  '/prep(.*)',
  '/resume(.*)',
  '/agents(.*)',
])

type PublicMetadata = { plan?: string; subscriptionStatus?: string }

function readPublicMetadata(sessionClaims: unknown): PublicMetadata | undefined {
  const claims = sessionClaims as Record<string, unknown> | null | undefined
  return (claims?.public_metadata ?? claims?.publicMetadata) as PublicMetadata | undefined
}

/**
 * Optional paywall: set CLERK_REQUIRE_ACTIVE_SUBSCRIPTION=true only when you enforce
 * Clerk Billing / publicMetadata in production. Default is off so a normal sign-in
 * unlocks the app; subscription can still be enforced in the API per feature.
 */
function isPaidAccess(metadata: PublicMetadata | undefined): boolean {
  if (metadata?.subscriptionStatus === 'active') return true
  if (metadata?.plan && metadata.plan !== 'free') return true
  return false
}

export default clerkMiddleware(async (auth, req) => {
  if (process.env.E2E_BYPASS_AUTH === '1') return
  if (!isProtectedRoute(req)) return

  await auth.protect()

  const strict = process.env.CLERK_REQUIRE_ACTIVE_SUBSCRIPTION === 'true'
  if (!strict) return

  const { sessionClaims } = await auth()
  const metadata = readPublicMetadata(sessionClaims)

  if (!isPaidAccess(metadata)) {
    return NextResponse.redirect(new URL('/', req.url))
  }
})

export const config = {
  matcher: ['/((?!_next|.*\\..*).*)'],
}
