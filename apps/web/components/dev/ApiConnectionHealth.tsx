'use client'

import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function shouldShowPanel(): boolean {
  return (
    process.env.NODE_ENV === 'development' ||
    process.env.NEXT_PUBLIC_CONNECTION_HEALTH === 'true'
  )
}

function ClerkSessionLine() {
  const { isLoaded, isSignedIn } = useAuth()
  if (!isLoaded) {
    return <span className="text-slate-400">Session loading…</span>
  }
  return (
    <span className={cn(isSignedIn ? 'text-emerald-700' : 'text-amber-700')}>
      {isSignedIn ? 'Signed in' : 'Signed out'}
    </span>
  )
}

function ApiConnectionHealthInner({ showAuthLine }: { showAuthLine: boolean }) {
  const [status, setStatus] = useState<'idle' | 'checking' | 'ok' | 'error'>('checking')
  const [ms, setMs] = useState<number | null>(null)
  const [lastError, setLastError] = useState<string>('')

  const check = useCallback(async () => {
    setStatus('checking')
    setLastError('')
    const t0 = typeof performance !== 'undefined' ? performance.now() : 0
    try {
      const res = await fetch(`${BASE.replace(/\/$/, '')}/healthz`, {
        method: 'GET',
        credentials: 'omit',
      })
      const elapsed =
        typeof performance !== 'undefined' ? Math.round(performance.now() - t0) : null
      setMs(elapsed)
      if (!res.ok) {
        setStatus('error')
        setLastError(`HTTP ${res.status}`)
        return
      }
      const json = (await res.json().catch(() => ({}))) as { status?: string }
      if (json.status === 'ok') {
        setStatus('ok')
      } else {
        setStatus('error')
        setLastError('Unexpected body')
      }
    } catch (e) {
      setStatus('error')
      setMs(null)
      setLastError(e instanceof Error ? e.message : 'Network error')
    }
  }, [])

  useEffect(() => {
    void check()
    const id = window.setInterval(() => void check(), 60_000)
    return () => window.clearInterval(id)
  }, [check])

  const hostLabel = (() => {
    try {
      return new URL(BASE).host || BASE
    } catch {
      return BASE
    }
  })()

  return (
    <div
      className="mx-3 mb-2 rounded-lg border border-slate-200 bg-white/95 px-2.5 py-2 shadow-sm"
      aria-label="API connection status"
    >
      <p className="truncate font-mono text-[10px] text-slate-500" title={BASE}>
        {hostLabel}
      </p>
      <div className="mt-1.5 flex flex-wrap items-center justify-between gap-x-2 gap-y-1 text-[11px]">
        <span
          className={cn(
            'font-medium',
            status === 'ok' && 'text-emerald-700',
            status === 'error' && 'text-rose-700',
            (status === 'idle' || status === 'checking') && 'text-slate-500',
          )}
        >
          API {status === 'checking' ? '…' : status === 'ok' ? 'reachable' : status === 'error' ? 'unreachable' : '—'}
          {ms != null && status === 'ok' ? ` · ${ms}ms` : null}
          {status === 'error' && lastError ? ` · ${lastError}` : null}
        </span>
        {showAuthLine ? <ClerkSessionLine /> : <span className="text-slate-400">No Clerk</span>}
      </div>
      <button
        type="button"
        onClick={() => void check()}
        className="mt-2 flex w-full items-center justify-center gap-1 rounded border border-slate-200 bg-slate-50 py-1 text-[10px] font-medium text-slate-700 hover:bg-slate-100"
      >
        <RefreshCw size={10} aria-hidden />
        Retry check
      </button>
    </div>
  )
}

/**
 * Dev-time (or NEXT_PUBLIC_CONNECTION_HEALTH=true) panel: pings API /healthz and shows Clerk session when enabled.
 */
export default function ApiConnectionHealthGate() {
  if (!shouldShowPanel()) {
    return null
  }
  const showAuthLine = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY)
  return <ApiConnectionHealthInner showAuthLine={showAuthLine} />
}
