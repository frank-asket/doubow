import { redirect } from 'next/navigation'
import type { Route } from 'next'

/** Legacy URL from marketing — subscription UI lives under the dashboard. */
export default function SubscribeRedirect() {
  redirect('/billing' as Route)
}
