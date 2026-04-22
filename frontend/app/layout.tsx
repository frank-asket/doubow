import type { Metadata } from 'next'
import { Suspense } from 'react'
import { ClerkProvider } from '@clerk/nextjs'
import { Plus_Jakarta_Sans } from 'next/font/google'
import ClerkApiAuthBridge from '@/components/auth/ClerkApiAuthBridge'
import ClerkDevOriginGuard from '@/components/auth/ClerkDevOriginGuard'
import DevAuthNotice from '@/components/auth/DevAuthNotice'
import PostHogProvider from '@/components/analytics/PostHogProvider'
import { ThemeProvider } from '@/components/theme/ThemeProvider'
import './globals.css'

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Doubow — The platform for your next job or venture',
  description:
    "Doubow builds your professional profile and automates tailored drafts, pipeline tracking, and interview prep—whether you're chasing a dream job or starting something of your own. You review and submit on official channels; nothing goes out without you.",
  icons: { icon: '/favicon.svg' },
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
        className={`${plusJakartaSans.variable} flex min-h-full flex-col font-sans antialiased`}
        suppressHydrationWarning
      >
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
              <ClerkDevOriginGuard />
              <ClerkApiAuthBridge />
              <DevAuthNotice />
              <PostHogBoundary />
              {children}
            </ThemeProvider>
          </ClerkProvider>
        ) : (
          <ThemeProvider>
            <ClerkDevOriginGuard />
            <PostHogBoundary />
            {children}
          </ThemeProvider>
        )}
      </body>
    </html>
  )
}
