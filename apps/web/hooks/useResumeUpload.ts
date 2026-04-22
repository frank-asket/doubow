import { useCallback, useState } from 'react'

import { resumeApi } from '@/lib/api'
import { setActivationStartNow, trackEvent } from '@/lib/telemetry'

export function useResumeUpload() {
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const upload = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    trackEvent('resume_upload_started', {
      file_name: file.name,
      file_size_bytes: file.size,
      file_type: file.type || 'unknown',
    })
    try {
      await resumeApi.upload(file)
      setActivationStartNow()
      trackEvent('resume_upload_succeeded', {
        file_name: file.name,
        file_size_bytes: file.size,
      })
      return { success: true }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setError(message)
      return { success: false }
    } finally {
      setUploading(false)
    }
  }, [])

  const analyzeWithAI = useCallback(async () => {
    setAnalyzing(true)
    setAnalysis('')
    try {
      const result = await resumeApi.analyzeProfile()
      setAnalysis(result.analysis)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Analysis failed'
      setAnalysis(`Error: ${message}`)
    } finally {
      setAnalyzing(false)
    }
  }, [])

  return { upload, uploading, analyzeWithAI, analyzing, analysis, error }
}
