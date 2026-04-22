import { Settings } from 'lucide-react'

import AiConfigDebugCard from '@/components/settings/AiConfigDebugCard'
import ConnectGmailCard from '@/components/settings/ConnectGmailCard'

export default function SettingsPage() {
  const showAiDebugCard = process.env.NODE_ENV !== 'production'

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <header className="flex items-center gap-3">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-zinc-200 text-zinc-700">
          <Settings size={18} />
        </div>
        <div>
          <h1 className="text-[30px] font-semibold tracking-tight text-zinc-900">Settings</h1>
          <p className="text-sm text-zinc-500">Manage account and dashboard preferences.</p>
        </div>
      </header>

      <section className="grid gap-4 lg:grid-cols-2">
        <ConnectGmailCard />
        {showAiDebugCard ? <AiConfigDebugCard /> : null}
        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <h2 className="text-sm font-semibold text-zinc-900">Notifications</h2>
          <p className="mt-1 text-sm text-zinc-600">Email and in-app alert preferences.</p>
          <p className="mt-3 text-xs text-zinc-500">This panel is ready for wiring to backend preferences.</p>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <h2 className="text-sm font-semibold text-zinc-900">Appearance</h2>
          <p className="mt-1 text-sm text-zinc-600">Theme and dashboard layout options.</p>
          <p className="mt-3 text-xs text-zinc-500">Use this route as the canonical settings surface.</p>
        </article>
      </section>
    </div>
  )
}
