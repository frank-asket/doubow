import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/discover(.*)',
  '/pipeline(.*)',
  '/approvals(.*)',
  '/prep(.*)',
  '/resume(.*)',
  '/messages(.*)',
  '/agents(.*)',
  '/settings(.*)',
  '/notifications(.*)',
  '/search(.*)',
])
const isAuthEntryRoute = createRouteMatcher([
  '/auth(.*)',
  '/login(.*)',
  '/sign-in(.*)',
  '/sign-up(.*)',
])

/**
 * Auth only: guests -> sign-in for app routes; signed-in users skip marketing `/`.
 * Subscription / plan limits belong on the API (see backend), not proxy redirects.
 */
function isNextOrStaticAsset(pathname: string): boolean {
  if (pathname.startsWith('/_next')) return true
  // Next dev introspection / overlay
  if (pathname.startsWith('/__nextjs')) return true
  if (pathname === '/favicon.ico') return true
  return /\.(?:ico|png|jpg|jpeg|gif|svg|webp|woff2?|ttf|eot)$/i.test(pathname)
}

export default clerkMiddleware(async (auth, req) => {
  // Defense-in-depth: never run auth on Next internals or static assets.
  if (isNextOrStaticAsset(req.nextUrl.pathname)) return

  if (process.env.E2E_BYPASS_AUTH === '1') return
  const { userId } = await auth()

  // Signed-in users use the app only; marketing landing is for signed-out visitors.
  if (userId && req.nextUrl.pathname === '/') {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

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
})

export const config = {
  matcher: [
    // Never run auth on Next.js internals.
    '/((?!_next/static|_next/image|_next/webpack-hmr|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)',
  ],
}
