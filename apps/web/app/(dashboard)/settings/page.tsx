'use client'

import { useCallback, useState } from 'react'
import { ApiError, googleIntegrationsApi, linkedinIntegrationsApi } from '@/lib/api'

export default function SettingsPage() {
  const [reconnectBusy, setReconnectBusy] = useState<'google' | 'linkedin' | null>(null)
  const [reconnectError, setReconnectError] = useState<string | null>(null)

  const startReconnect = useCallback(async (provider: 'google' | 'linkedin') => {
    setReconnectError(null)
    setReconnectBusy(provider)
    try {
      const { authorization_url } =
        provider === 'google'
          ? await googleIntegrationsApi.getAuthorizationUrl()
          : await linkedinIntegrationsApi.getAuthorizationUrl()
      window.location.assign(authorization_url)
    } catch (e) {
      const fallback =
        provider === 'google' ? 'Could not start Gmail reconnect.' : 'Could not start LinkedIn reconnect.'
      setReconnectError(e instanceof ApiError ? e.detail : fallback)
      setReconnectBusy(null)
    }
  }, [])

  return (
    <div className="mx-auto max-w-5xl space-y-4 bg-[#f5faf8] px-4 py-4 dark:bg-transparent sm:px-6">
      <section className="border-b border-[0.5px] border-[rgba(188,201,198,0.9)] pb-3 dark:border-slate-700">
        <h1 className="text-[20px] font-medium leading-[1.02] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">
          Settings &amp; Integrations
        </h1>
        <p className="mt-1 text-[13px] text-[#6d7a77] dark:text-slate-400">
          Manage identity integrations used for approvals and outreach handoff.
        </p>
      </section>

      {reconnectError ? (
        <p
          className="border border-amber-300/60 bg-amber-50/50 px-3 py-2 text-xs text-amber-900 dark:border-amber-500/40 dark:bg-amber-950/30 dark:text-amber-200"
          role="alert"
        >
          {reconnectError}
        </p>
      ) : null}

      <section className="space-y-3">
        <article className="flex items-start justify-between border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div>
            <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
              Gmail Service
            </p>
            <p className="mt-1 text-[13px] text-[#171d1c] dark:text-slate-100">
              Reconnect Gmail if email draft handoff stops working.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void startReconnect('google')}
            disabled={reconnectBusy !== null}
            className="h-8 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#00685f] disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-teal-400"
          >
            Reconnect
          </button>
        </article>

        <article className="flex items-start justify-between border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div>
            <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
              LinkedIn Service
            </p>
            <p className="mt-1 text-[13px] text-[#171d1c] dark:text-slate-100">
              Reconnect LinkedIn when profile sync or handoff needs reauthorization.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void startReconnect('linkedin')}
            disabled={reconnectBusy !== null}
            className="h-8 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#00685f] disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-teal-400"
          >
            Reconnect
          </button>
        </article>
      </section>

      <section className="border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
          Account Actions
        </h2>
        <p className="mt-2 text-[13px] text-[#3d4947] dark:text-slate-400">
          Need account export or deactivation? Contact support and we will process your request.
        </p>
        <a
          href="mailto:support@doubow.com?subject=Account%20request"
          className="mt-3 inline-flex h-8 items-center justify-center border border-[0.5px] border-[#00685f] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#00685f] dark:border-teal-500 dark:text-teal-300"
        >
          Contact support
        </a>
      </section>
    </div>
  )
}
