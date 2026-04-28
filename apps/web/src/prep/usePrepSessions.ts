'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Application, PrepSession } from '@doubow/shared'
import { ApiError, applicationsApi, prepApi } from '../../lib/api'

export function usePrepSessions(initialApplicationId?: string) {
  const [apps, setApps] = useState<Application[]>([])
  const [sessions, setSessions] = useState<PrepSession[]>([])
  const [selectedAppId, setSelectedAppId] = useState(initialApplicationId ?? '')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const appRes = await applicationsApi.list()
      const userApps = appRes.items
      setApps(userApps)
      const targetAppId = selectedAppId || initialApplicationId || userApps[0]?.id || ''
      setSelectedAppId(targetAppId)

      if (!targetAppId) {
        setSessions([])
        return
      }

      try {
        const session = await prepApi.getForApplication(targetAppId)
        setSessions([session])
      } catch (e) {
        // 404 means prep has not been generated for this application yet.
        if (e instanceof ApiError && e.status === 404) {
          setSessions([])
          return
        }
        throw e
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Could not load prep sessions.')
    } finally {
      setLoading(false)
    }
  }, [initialApplicationId, selectedAppId])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!initialApplicationId) return
    setSelectedAppId(initialApplicationId)
  }, [initialApplicationId])

  const selectedSession = useMemo(() => {
    if (!sessions.length) return null
    if (!selectedAppId) return sessions[0]
    return sessions.find((s) => s.application.id === selectedAppId) ?? sessions[0]
  }, [sessions, selectedAppId])

  const generateForSelected = useCallback(async () => {
    if (!selectedAppId) return null
    setGenerating(true)
    setError(null)
    try {
      const generated = await prepApi.generate(selectedAppId)
      setSessions((prev) => [generated, ...prev.filter((p) => p.application.id !== generated.application.id)])
      return generated
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Prep generation failed.')
      return null
    } finally {
      setGenerating(false)
    }
  }, [selectedAppId])

  return {
    apps,
    sessions,
    selectedAppId,
    setSelectedAppId,
    selectedSession,
    loading,
    generating,
    error,
    setError,
    generateForSelected,
    reload: load,
  }
}
