import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { isPaidPublicMetadata, type ClerkPlanPublicMetadata } from '@/lib/clerkPlan'

const isProtectedRoute = createRouteMatcher([
  '/discover(.*)',
  '/pipeline(.*)',
  '/approvals(.*)',
  '/prep(.*)',
  '/resume(.*)',
  '/agents(.*)',
])
const isAuthEntryRoute = createRouteMatcher([
  '/auth(.*)',
  '/login(.*)',
  '/sign-in(.*)',
  '/sign-up(.*)',
])

function readPublicMetadata(sessionClaims: unknown): ClerkPlanPublicMetadata | undefined {
  const claims = sessionClaims as Record<string, unknown> | null | undefined
  return (claims?.public_metadata ?? claims?.publicMetadata) as
    | ClerkPlanPublicMetadata
    | undefined
}

/**
 * Optional paywall: set CLERK_REQUIRE_ACTIVE_SUBSCRIPTION=true only when you enforce
 * Clerk Billing / publicMetadata in production. Default is off so a normal sign-in
 * unlocks the app; subscription can still be enforced in the API per feature.
 */
export default clerkMiddleware(async (auth, req) => {
  if (process.env.E2E_BYPASS_AUTH === '1') return
  const { userId } = await auth()

  // Hard server-side guard: never mount auth pages when already signed in.
  if (userId && isAuthEntryRoute(req)) {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

  if (!isProtectedRoute(req)) return

  // Force local auth route instead of Clerk-hosted sign-in pages.
  if (!userId) {
    const signInUrl = new URL('/auth/sign-in', req.url)
    signInUrl.searchParams.set('redirect_url', req.url)
    return NextResponse.redirect(signInUrl)
  }

  const strict = process.env.CLERK_REQUIRE_ACTIVE_SUBSCRIPTION === 'true'
  if (!strict) return

  const { sessionClaims } = await auth()
  const metadata = readPublicMetadata(sessionClaims)

  if (!isPaidPublicMetadata(metadata)) {
    return NextResponse.redirect(new URL('/', req.url))
  }
})

export const config = {
  matcher: ['/((?!_next|.*\\..*).*)'],
}
