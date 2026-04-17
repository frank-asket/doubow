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

export default clerkMiddleware(async (auth, req) => {
  if (!isProtectedRoute(req)) return

  await auth.protect()

  const { sessionClaims } = await auth()
  const metadata =
    (sessionClaims?.public_metadata as { plan?: string; subscriptionStatus?: string } | undefined) ??
    (sessionClaims?.publicMetadata as { plan?: string; subscriptionStatus?: string } | undefined)

  const hasSubscription =
    metadata?.subscriptionStatus === 'active' || (!!metadata?.plan && metadata.plan !== 'free')

  if (!hasSubscription && req.nextUrl.pathname !== '/subscribe') {
    return NextResponse.redirect(new URL('/subscribe', req.url))
  }
})

export const config = {
  matcher: ['/((?!_next|.*\\..*).*)'],
}
