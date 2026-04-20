import type { Metadata } from 'next'
import { ClerkProvider } from '@clerk/nextjs'
import { Plus_Jakarta_Sans } from 'next/font/google'
import ClerkApiAuthBridge from '@/components/auth/ClerkApiAuthBridge'
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
  icons: { icon: '/favicon.ico' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${plusJakartaSans.variable} flex min-h-full flex-col bg-black font-sans text-zinc-50 antialiased`}
        suppressHydrationWarning
      >
        {clerkPublishableKey ? (
          <ClerkProvider publishableKey={clerkPublishableKey}>
            <ClerkApiAuthBridge />
            {children}
          </ClerkProvider>
        ) : (
          children
        )}
      </body>
    </html>
  )
}
