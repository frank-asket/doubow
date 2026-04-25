import type { ReactNode } from 'react'

/** Billing uses Clerk (`useUser`); skip static prerender so build does not run without ClerkProvider. */
export const dynamic = 'force-dynamic'

export default function BillingLayout({ children }: { children: ReactNode }) {
  return children
}
