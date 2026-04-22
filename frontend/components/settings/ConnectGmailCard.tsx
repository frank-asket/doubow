'use client'

import { useCallback, useEffect, useState } from 'react'
import { Mail } from 'lucide-react'

import { ApiError, googleIntegrationsApi } from '@/lib/api'

export default function ConnectGmailCard() {
  const [status, setStatus] = useState<{ connected: boolean; google_email: string | null } | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [banner, setBanner] = useState<{ type: 'ok' | 'err'; msg: string } | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const connected = params.get('google_connected')
    const googleErr = params.get('google_error')
    if (connected === '1') {
      setBanner({
        type: 'ok',
        msg:
          'Google connected. After approving an email draft, Doubow can save it to your Gmail Drafts or send via Gmail—depending on server settings. If we add new Gmail permissions, use Disconnect then Connect again.',
      })
      window.history.replaceState(null, '', window.location.pathname)
    } else if (googleErr) {
      setBanner({
        type: 'err',
        msg: `Could not connect Gmail (${googleErr}). Try again or check server OAuth settings.`,
      })
      window.history.replaceState(null, '', window.location.pathname)
    }
  }, [])

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const s = await googleIntegrationsApi.status()
      setStatus(s)
      setError(null)
    } catch (e) {
      setStatus(null)
      setError(e instanceof ApiError ? e.detail : 'Could not load Gmail status.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const connect = async () => {
    try {
      setBusy(true)
      const { authorization_url } = await googleIntegrationsApi.getAuthorizationUrl()
      window.location.assign(authorization_url)
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 503
          ? 'Gmail linking is not configured on the API (set Google OAuth env vars).'
          : e instanceof ApiError
            ? e.detail
            : 'Could not start Google sign-in.',
      )
      setBusy(false)
    }
  }

  const disconnect = async () => {
    try {
      setBusy(true)
      await googleIntegrationsApi.disconnect()
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Disconnect failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
      <div className="flex items-start gap-3">
        <div className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-zinc-700">
          <Mail size={18} aria-hidden />
        </div>
        <div className="min-w-0 flex-1 space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-zinc-900">Google & Gmail</h2>
            <p className="mt-1 text-sm text-zinc-600">
              Connect Google so Doubow can use your Gmail account after you approve drafts—typically saving to{' '}
              <strong className="font-medium text-zinc-800">Drafts</strong> for you to edit and send from your own address,
              or sending directly when configured on the API.
            </p>
            <p className="mt-2 text-xs leading-relaxed text-zinc-500">
              If you connected before your team enabled “compose” permissions, reconnect here so Gmail can create drafts.
              In Google Cloud Console, add the Gmail compose/send scopes your app uses to the OAuth consent screen (production
              may require verification).
            </p>
          </div>

          {banner && (
            <p
              role="status"
              className={
                banner.type === 'ok'
                  ? 'rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-900'
                  : 'rounded-lg bg-red-50 px-3 py-2 text-sm text-red-900'
              }
            >
              {banner.msg}
            </p>
          )}

          {error && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-950" role="alert">
              {error}
            </p>
          )}

          {loading ? (
            <p className="text-xs text-zinc-500">Checking connection…</p>
          ) : status?.connected ? (
            <div className="flex flex-wrap items-center gap-3">
              <div className="space-y-1">
                <p className="text-sm text-zinc-700">
                  Connected as <span className="font-medium">{status.google_email ?? 'your Google account'}</span>
                </p>
                <p className="text-xs text-zinc-500">
                  Drafts or send not working after an upgrade? Disconnect and connect again to refresh Gmail permissions.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void disconnect()}
                disabled={busy}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-800 transition hover:bg-zinc-50 disabled:opacity-50"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => void connect()}
              disabled={busy}
              className="inline-flex items-center justify-center rounded-lg bg-[#1f3dbf] px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-[#2744cf] disabled:opacity-50"
            >
              Connect Gmail
            </button>
          )}
        </div>
      </div>
    </article>
  )
}
