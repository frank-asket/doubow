import type { Metadata } from 'next'
import { Suspense } from 'react'
import { ClerkProvider } from '@clerk/nextjs'
import { Fraunces, Plus_Jakarta_Sans } from 'next/font/google'
import ClerkApiAuthBridge from '@/components/auth/ClerkApiAuthBridge'
import ClerkDevOriginGuard from '@/components/auth/ClerkDevOriginGuard'
import PostHogProvider from '@/components/analytics/PostHogProvider'
import StubApiRuntimeFlag from '@/components/dev/StubApiRuntimeFlag'
import MotionProvider from '@/components/motion/MotionProvider'
import { ThemeProvider } from '@/components/theme/ThemeProvider'
import './globals.css'

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

/** Editorial display for marketing headlines (landing); body stays sans. */
const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://doubow.vercel.app'),
  title: 'Doubow — The platform for your next job or venture',
  description:
    "Doubow builds your professional profile and automates tailored drafts, pipeline tracking, and interview prep—whether you're chasing a dream job or starting something of your own. You review and submit on official channels; nothing goes out without you.",
  icons: { icon: '/favicon.svg' },
  openGraph: {
    title: 'Doubow — The platform for your next job or venture',
    description:
      "Doubow builds your professional profile and automates tailored drafts, pipeline tracking, and interview prep. You review and submit on official channels.",
    url: '/',
    siteName: 'Doubow',
    type: 'website',
    images: [{ url: '/favicon.svg', alt: 'Doubow logo' }],
  },
  twitter: {
    card: 'summary',
    title: 'Doubow — The platform for your next job or venture',
    description:
      "Doubow builds your professional profile and automates tailored drafts, pipeline tracking, and interview prep. You stay in control of every send.",
    images: ['/favicon.svg'],
  },
}

function PostHogBoundary() {
  return (
    <Suspense fallback={null}>
      <PostHogProvider />
    </Suspense>
  )
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${plusJakartaSans.variable} ${fraunces.variable} flex min-h-full flex-col font-sans antialiased`}
        suppressHydrationWarning
      >
        <StubApiRuntimeFlag />
        {clerkPublishableKey ? (
          <ClerkProvider
            publishableKey={clerkPublishableKey}
            signInUrl="/auth/sign-in"
            signUpUrl="/auth/sign-up"
            signInFallbackRedirectUrl="/dashboard"
            signUpFallbackRedirectUrl="/dashboard"
            afterSignOutUrl="/"
          >
            <ThemeProvider>
              <MotionProvider>
                <ClerkDevOriginGuard />
                <ClerkApiAuthBridge />
                <PostHogBoundary />
                {children}
              </MotionProvider>
            </ThemeProvider>
          </ClerkProvider>
        ) : (
          <ThemeProvider>
            <MotionProvider>
              <ClerkDevOriginGuard />
              <PostHogBoundary />
              {children}
            </MotionProvider>
          </ThemeProvider>
        )}
      </body>
    </html>
  )
}
