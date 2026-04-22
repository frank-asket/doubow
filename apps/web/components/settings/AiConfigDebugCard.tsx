'use client'

import { useCallback, useEffect, useState } from 'react'
import { Bot } from 'lucide-react'

import { ApiError, authApi } from '@/lib/api'

type AiConfig = {
  openrouter_configured: boolean
  openrouter_api_url: string
  openrouter_http_referer: string | null
  resolved_models: Record<string, string>
}

export default function AiConfigDebugCard() {
  const [config, setConfig] = useState<AiConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const data = await authApi.aiConfig()
      setConfig(data)
      setError(null)
    } catch (e) {
      setConfig(null)
      setError(e instanceof ApiError ? e.detail : 'Could not load AI configuration.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
      <div className="flex items-start gap-3">
        <div className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-zinc-700">
          <Bot size={18} aria-hidden />
        </div>
        <div className="min-w-0 flex-1 space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-zinc-900">AI Model Routing (Debug)</h2>
            <p className="mt-1 text-sm text-zinc-600">
              Verifies active OpenRouter model resolution from the authenticated backend session.
            </p>
          </div>

          {error && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-950" role="alert">
              {error}
            </p>
          )}

          {loading ? (
            <p className="text-xs text-zinc-500">Loading AI configuration…</p>
          ) : config ? (
            <div className="space-y-3 text-sm">
              <p className="text-zinc-700">
                OpenRouter configured:{' '}
                <span className={config.openrouter_configured ? 'font-medium text-emerald-700' : 'font-medium text-zinc-600'}>
                  {config.openrouter_configured ? 'yes' : 'no'}
                </span>
              </p>
              <div className="rounded-lg bg-zinc-50 p-3 text-xs text-zinc-700">
                <p>
                  <span className="font-medium">API URL:</span> {config.openrouter_api_url}
                </p>
                <p className="mt-1">
                  <span className="font-medium">Referer:</span> {config.openrouter_http_referer ?? 'not set'}
                </p>
              </div>
              <div className="rounded-lg border border-zinc-200 p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Resolved models</p>
                <ul className="mt-2 space-y-1 text-xs text-zinc-700">
                  {Object.entries(config.resolved_models).map(([useCase, model]) => (
                    <li key={useCase}>
                      <span className="font-medium">{useCase}:</span> {model}
                    </li>
                  ))}
                </ul>
              </div>
              <button
                type="button"
                onClick={() => void load()}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-800 transition hover:bg-zinc-50"
              >
                Refresh
              </button>
            </div>
          ) : (
            <p className="text-xs text-zinc-500">No configuration returned.</p>
          )}
        </div>
      </div>
    </article>
  )
}
