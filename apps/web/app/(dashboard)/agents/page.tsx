import { redirect } from 'next/navigation'

/** Unified Assistant lives at `/messages`; `/agents` kept as a redirect for bookmarks and old links. */
export default function AgentsRedirectPage() {
  redirect('/messages')
}
