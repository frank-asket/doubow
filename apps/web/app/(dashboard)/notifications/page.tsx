import { redirect } from 'next/navigation'
import type { Route } from 'next'

export default function NotificationsPage() {
  redirect('/messages' as Route)
}
