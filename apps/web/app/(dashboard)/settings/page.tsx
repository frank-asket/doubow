'use client'

import { useCallback, useState } from 'react'
import useSWR from 'swr'
import { ApiError, googleIntegrationsApi, jobAlertsApi, linkedinIntegrationsApi } from '@/lib/api'
import { trackEvent } from '@/lib/telemetry'

export default function SettingsPage() {
  const [reconnectBusy, setReconnectBusy] = useState<'google' | 'linkedin' | null>(null)
  const [reconnectError, setReconnectError] = useState<string | null>(null)
  const [alertsPage, setAlertsPage] = useState(1)
  const {
    data: alertsFeed,
    isLoading: alertsLoading,
    error: alertsError,
  } = useSWR(
    ['job-alerts-feed', alertsPage],
    ([, page]) => jobAlertsApi.feed({ page, per_page: 8 }),
    { revalidateOnFocus: false },
  )

  const startReconnect = useCallback(async (provider: 'google' | 'linkedin') => {
    trackEvent('settings_reconnect_clicked', { provider })
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
          Connect the accounts Doubow uses when you approve emails or LinkedIn steps.
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
              Reconnect if approved emails stop sending or drafts get stuck.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void startReconnect('google')}
            disabled={reconnectBusy !== null}
            className="h-8 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary-green disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-emerald-400"
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
              Reconnect if LinkedIn asks you to sign in again or linked steps fail.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void startReconnect('linkedin')}
            disabled={reconnectBusy !== null}
            className="h-8 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary-green disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-emerald-400"
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
          onClick={() => trackEvent('settings_contact_support_clicked', { source: 'settings_account_actions' })}
          className="mt-3 inline-flex h-8 items-center justify-center border border-[0.5px] border-primary-green px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary-green dark:border-secondary-green dark:text-emerald-300"
        >
          Contact support
        </a>
      </section>

      <section className="border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
          Job Alerts History
        </h2>
        <p className="mt-2 text-[13px] text-[#3d4947] dark:text-slate-400">
          Delivered alert items based on your fit score and resume profile.
        </p>

        {alertsLoading ? (
          <p className="mt-3 text-xs text-[#6d7a77] dark:text-slate-400">Loading recent alerts…</p>
        ) : alertsError ? (
          <p className="mt-3 text-xs text-amber-700 dark:text-amber-300">
            Could not load alerts history right now.
          </p>
        ) : alertsFeed?.items.length ? (
          <>
            <ul className="mt-3 space-y-2">
              {alertsFeed.items.map((item) => (
                <li
                  key={item.delivery_id}
                  className="rounded-sm border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-[#f7fbf9] p-3 dark:border-slate-700 dark:bg-slate-950/50"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-[13px] font-medium text-[#171d1c] dark:text-slate-100">
                      {item.title} @ {item.company}
                    </p>
                    <span className="text-[11px] font-semibold text-primary-green dark:text-emerald-300">
                      Fit {item.fit_score.toFixed(1)}/5
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-[#6d7a77] dark:text-slate-400">
                    Delivered {new Date(item.delivered_at).toLocaleString()}
                    {item.location ? ` · ${item.location}` : ''}
                  </p>
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-flex text-[11px] font-semibold text-primary-green hover:underline dark:text-emerald-300"
                    >
                      Open job listing ↗
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
            <div className="mt-3 flex items-center justify-between">
              <p className="text-[11px] text-[#6d7a77] dark:text-slate-400">
                Showing page {alertsFeed.page} of {Math.max(1, Math.ceil(alertsFeed.total / alertsFeed.per_page))}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setAlertsPage((p) => Math.max(1, p - 1))}
                  disabled={alertsFeed.page <= 1}
                  className="h-8 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary-green disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-emerald-400"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setAlertsPage((p) => p + 1)}
                  disabled={alertsFeed.page * alertsFeed.per_page >= alertsFeed.total}
                  className="h-8 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary-green disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-emerald-400"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        ) : (
          <p className="mt-3 text-xs text-[#6d7a77] dark:text-slate-400">
            No delivered alerts yet. Once alerts run, matched jobs will appear here.
          </p>
        )}
      </section>
    </div>
  )
}
