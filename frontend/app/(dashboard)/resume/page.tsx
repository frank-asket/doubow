'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { Upload, FileText, CheckCircle, Loader2, Sparkles, X, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useResumeUpload } from '@/hooks/useResumeUpload'
import { resumeApi } from '@/lib/api'
import type { UserPreferences } from '@/types'

const SENIORITY_OPTIONS = ['Junior', 'Mid', 'Senior', 'Lead', 'Staff', 'Principal']
const DEFAULT_PREFS: UserPreferences = {
  target_role: 'AI/ML Engineer',
  location: 'Remote / Europe',
  min_salary: 140000,
  seniority: 'Senior',
  skills: ['RAG', 'LLMs', 'Python', 'FastAPI', 'MLOps'],
}

export default function ResumePage() {
  const { upload, uploading, analyzeWithAI, analyzing, analysis, error: uploadError } = useResumeUpload()
  const [uploaded, setUploaded] = useState(false)
  const [fileName, setFileName] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [resumeExists, setResumeExists] = useState(false)

  const [role, setRole] = useState(DEFAULT_PREFS.target_role)
  const [location, setLocation] = useState(DEFAULT_PREFS.location)
  const [salary, setSalary] = useState(String(DEFAULT_PREFS.min_salary ?? ''))
  const [seniority, setSeniority] = useState(DEFAULT_PREFS.seniority)
  const [skills, setSkills] = useState(DEFAULT_PREFS.skills.join(', '))
  const [savedPrefs, setSavedPrefs] = useState<UserPreferences>(DEFAULT_PREFS)
  const [savingPrefs, setSavingPrefs] = useState(false)
  const [prefsStatus, setPrefsStatus] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const hydrateFromPrefs = useCallback((prefs: UserPreferences) => {
    setRole(prefs.target_role ?? '')
    setLocation(prefs.location ?? '')
    setSalary(prefs.min_salary !== undefined ? String(prefs.min_salary) : '')
    setSeniority(prefs.seniority ?? 'Mid')
    setSkills((prefs.skills ?? []).join(', '))
  }, [])

  const loadResume = useCallback(async () => {
    setLoadingProfile(true)
    try {
      const profile = await resumeApi.get()
      setResumeExists(true)
      setUploaded(true)
      setFileName(profile.file_name)
      setSavedPrefs(profile.preferences)
      hydrateFromPrefs(profile.preferences)
      setPrefsStatus(null)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load resume profile'
      if (msg.toLowerCase().includes('resume not found')) {
        setResumeExists(false)
      } else {
        setPrefsStatus({ type: 'error', text: msg })
      }
    } finally {
      setLoadingProfile(false)
    }
  }, [hydrateFromPrefs])

  useEffect(() => {
    loadResume()
  }, [loadResume])

  const savePreferences = useCallback(async () => {
    setSavingPrefs(true)
    setPrefsStatus(null)
    try {
      const parsedSalary = salary.trim() === '' ? undefined : Number(salary)
      const payload: Partial<UserPreferences> = {
        target_role: role.trim(),
        location: location.trim(),
        min_salary: Number.isFinite(parsedSalary) ? parsedSalary : undefined,
        seniority: seniority as UserPreferences['seniority'],
        skills: skills.split(',').map((s) => s.trim()).filter(Boolean),
      }
      const updated = await resumeApi.updatePreferences(payload)
      setSavedPrefs(updated)
      hydrateFromPrefs(updated)
      setPrefsStatus({ type: 'success', text: 'Preferences saved.' })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save preferences'
      setPrefsStatus({ type: 'error', text: msg })
    } finally {
      setSavingPrefs(false)
    }
  }, [role, location, salary, seniority, skills, hydrateFromPrefs])

  const handleFile = useCallback(async (file: File) => {
    if (!file) return
    setFileName(file.name)
    const result = await upload(file)
    if (result.success) {
      setResumeExists(true)
      setUploaded(true)
      setPrefsStatus({ type: 'success', text: 'Resume uploaded. Preferences are ready to save.' })
      await loadResume()
    }
  }, [upload, loadResume])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <section className="rounded-3xl border border-zinc-800 bg-[#080808] p-5 sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Resume</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">My resume</h1>
        <p className="mt-2 text-sm text-zinc-400 sm:text-base">Upload your resume to power matching, tailoring, and interview prep</p>
      </section>

      {/* Upload zone */}
      <div
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 mb-6',
          dragOver ? 'border-emerald-500/40 bg-emerald-500/10' : uploaded ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-zinc-800 hover:border-zinc-700 hover:bg-zinc-950'
        )}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={28} className="animate-spin text-emerald-300" />
            <p className="text-sm text-zinc-300">Uploading {fileName}…</p>
          </div>
        ) : uploaded ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle size={28} className="text-emerald-300" />
            <div>
              <p className="text-sm font-medium text-zinc-100">{fileName}</p>
              <p className="mt-0.5 text-xs text-emerald-300">Uploaded successfully</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setUploaded(false); setFileName('') }}
              className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300"
            >
              <X size={11} /> Replace
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
              <Upload size={20} className="text-zinc-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-200">Drop your resume here</p>
              <p className="mt-1 text-xs text-zinc-500">PDF or DOCX · Up to 5 MB</p>
            </div>
          </div>
        )}
      </div>
      {uploadError && (
        <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3">
          <AlertCircle size={14} className="mt-0.5 flex-shrink-0 text-rose-300" />
          <p className="text-xs text-rose-300">{uploadError}</p>
        </div>
      )}

      {/* Preferences */}
      <div className="card p-5 mb-5">
        <p className="mb-4 text-sm font-medium text-zinc-100">Search preferences</p>
        {loadingProfile ? (
          <div className="mb-4 flex items-center gap-2 text-xs text-zinc-500">
            <Loader2 size={12} className="animate-spin" />
            Loading saved preferences...
          </div>
        ) : null}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-400">Target role</label>
            <input className="field text-sm" value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. ML Engineer" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-400">Location</label>
            <input className="field text-sm" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Remote, London" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-400">Min salary (USD)</label>
            <input className="field text-sm" value={salary} onChange={(e) => setSalary(e.target.value)} placeholder="e.g. 140000" type="number" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-400">Seniority</label>
            <select
              className="field text-sm"
              value={seniority}
              onChange={(e) => setSeniority(e.target.value as UserPreferences['seniority'])}
            >
              {SENIORITY_OPTIONS.map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="col-span-2">
            <label className="mb-1.5 block text-xs font-medium text-zinc-400">Key skills</label>
            <input className="field text-sm" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="e.g. RAG, LLMs, Python" />
          </div>
        </div>
        {prefsStatus && (
          <div
            className={cn(
              'flex items-start gap-2 text-xs rounded-md px-3 py-2 mt-4',
              prefsStatus.type === 'success'
                ? 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                : 'border border-rose-500/30 bg-rose-500/10 text-rose-300'
            )}
          >
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            <span>{prefsStatus.text}</span>
          </div>
        )}
        {!loadingProfile && !resumeExists && (
          <div className="mt-4 flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            <span>Upload a resume first to enable preference saving.</span>
          </div>
        )}
        <div className="mt-4 flex gap-2 border-t border-zinc-800 pt-4">
          <button
            onClick={() => savePreferences()}
            disabled={savingPrefs || loadingProfile || !resumeExists}
            className="btn btn-primary text-xs gap-1.5"
          >
            {savingPrefs ? <Loader2 size={12} className="animate-spin" /> : null}
            {savingPrefs ? 'Saving...' : 'Save preferences'}
          </button>
          <button
            onClick={() => {
              hydrateFromPrefs(savedPrefs)
              setPrefsStatus(null)
            }}
            disabled={savingPrefs || loadingProfile}
            className="btn text-xs"
          >
            Reset
          </button>
        </div>
      </div>

      {/* AI Analysis */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm font-medium text-zinc-100">AI profile analysis</p>
            <p className="mt-0.5 text-xs text-zinc-400">Get archetypes, skill gaps, and target companies</p>
          </div>
          <button
            onClick={() => analyzeWithAI()}
            disabled={analyzing}
            className="btn btn-primary text-xs gap-1.5"
          >
            {analyzing ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            {analyzing ? 'Analyzing…' : 'Analyze with AI'}
          </button>
        </div>

        <div className={cn(
          'min-h-[100px] rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-xs leading-relaxed whitespace-pre-wrap text-zinc-200',
          !analysis && 'flex items-center justify-center text-zinc-500'
        )}>
          {analysis || (
            <div className="text-center">
              <FileText size={20} className="mx-auto mb-2 opacity-40" />
              <p>Upload your resume and click Analyze to see your profile breakdown</p>
            </div>
          )}
          {analyzing && <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-emerald-300 align-middle" />}
        </div>
      </div>
    </div>
  )
}
