'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import useSWR from 'swr'

import { agentsApi, streamAgentStatus, streamOrchestratorChat } from '@/lib/api'
import { useAgentStore } from '@/stores/agentStore'
import type { AgentName } from '@/types'

export function useAgentStream() {
  const { setAgents, updateAgent } = useAgentStore()

  const { data } = useSWR('agents', agentsApi.status, {
    revalidateOnFocus: false,
    dedupingInterval: 60_000,
  })

  useEffect(() => {
    if (data) setAgents(data)
  }, [data, setAgents])

  useEffect(() => {
    const stop = streamAgentStatus((event) => {
      updateAgent(event.name as AgentName, event)
    })
    return stop
  }, [updateAgent])
}

export function useOrchestratorChat() {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'ai'; text: string }>>([])
  const [streaming, setStreaming] = useState(false)
  const stopRef = useRef<(() => void) | null>(null)

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return

    setMessages((m) => [...m, { role: 'user', text: trimmed }, { role: 'ai', text: '' }])
    setStreaming(true)
    let acc = ''

    stopRef.current = streamOrchestratorChat(
      trimmed,
      (chunk) => {
        acc += chunk
        setMessages((m) => [...m.slice(0, -1), { role: 'ai', text: acc }])
      },
      () => setStreaming(false),
      (error) => {
        setMessages((m) => [...m.slice(0, -1), { role: 'ai', text: `Error: ${error}` }])
        setStreaming(false)
      }
    )
  }, [])

  const stop = useCallback(() => {
    stopRef.current?.()
    setStreaming(false)
  }, [])

  return { messages, streaming, send, stop }
}
