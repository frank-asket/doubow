'use client'

import { useState } from 'react'

export function OrchestratorChat() {
  const [value, setValue] = useState('')
  return (
    <div className="card p-4">
      <p className="mb-2 text-sm font-medium">Orchestrator chat</p>
      <input className="field w-full" value={value} onChange={(e) => setValue(e.target.value)} placeholder="Ask about your pipeline" />
    </div>
  )
}
