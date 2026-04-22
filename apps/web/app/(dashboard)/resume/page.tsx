'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import { Upload, FileText, CheckCircle, Loader2, Sparkles, X, AlertCircle } from 'lucide-react'
import { DashboardPageHeader } from '@/components/dashboard/DashboardPageHeader'
import { cn } from '@/lib/utils'
import { useResumeUpload } from '@/hooks/useResumeUpload'
import { isE2EAuthBypass } from '@/lib/e2e'
import { ApiError, resumeApi } from '@/lib/api'
import type { UserPreferences } from '@doubow/shared'

const SENIORITY_OPTIONS = ['Junior', 'Mid', 'Senior', 'Lead', 'Staff', 'Principal']
const DEFAULT_PREFS: UserPreferences = {
  target_role: 'AI/ML Engineer',
  location: 'Remote / Europe',
  min_salary: 140000,
  seniority: 'Senior',
  skills: ['RAG', 'LLMs', 'Python', 'FastAPI', 'MLOps'],
}

export default function ResumePage() {
  const { isLoaded, isSignedIn } = useAuth()
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
    setSalary(prefs.min_salary != null && Number.isFinite(prefs.min_salary) ? String(prefs.min_salary) : '')
    setSeniority((prefs.seniority ?? 'Mid') as UserPreferences['seniority'])
    setSkills((prefs.skills ?? []).join(', '))
  }, [])

  const loadResume = useCallback(async () => {
    setLoadingProfile(true)
    try {
      const onboarding = await resumeApi.onboardingStatus()
      if (onboarding.state === 'no_resume') {
        setResumeExists(false)
        setUploaded(false)
        setFileName('')
        setPrefsStatus(null)
        return
      }
      const profile = await resumeApi.get()
      setResumeExists(true)
      setUploaded(true)
      setFileName(profile.file_name)
      setSavedPrefs(profile.preferences)
      hydrateFromPrefs(profile.preferences)
      setPrefsStatus(null)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load resume profile'
      if (err instanceof ApiError && err.status === 401) {
        setPrefsStatus({ type: 'error', text: 'Could not verify your session — refresh the page or sign in again.' })
      } else {
        setPrefsStatus({ type: 'error', text: msg })
      }
    } finally {
      setLoadingProfile(false)
    }
  }, [hydrateFromPrefs])

  useEffect(() => {
    if (isE2EAuthBypass()) {
      loadResume()
      return
    }
    if (!isLoaded) return
    if (!isSignedIn) {
      setLoadingProfile(false)
      return
    }
    loadResume()
  }, [isLoaded, isSignedIn, loadResume])

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
      setPrefsStatus({
        type: 'success',
        text: 'Resume uploaded. Search preferences were updated from your résumé — review below and save any tweaks.',
      })
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
    <div className="space-y-5 p-5 sm:p-7">
      <DashboardPageHeader
        kicker="Resume"
        title="My resume"
        description="Upload your resume to power matching, tailoring, and interview prep"
      />

      {/* Upload zone */}
      <div
        className={cn(
          'mb-6 cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all duration-200',
          dragOver || uploaded
            ? 'border-indigo-200 bg-indigo-50/60'
            : 'border-[#e7e8ee] hover:border-indigo-200 hover:bg-zinc-50',
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
            <Loader2 size={28} className="animate-spin text-indigo-600" />
            <p className="text-sm text-zinc-600">Uploading {fileName}…</p>
          </div>
        ) : uploaded ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle size={28} className="text-emerald-600" />
            <div>
              <p className="text-sm font-medium text-zinc-900">{fileName}</p>
              <p className="mt-0.5 text-xs text-zinc-600">Uploaded successfully</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setUploaded(false); setFileName('') }}
              className="flex items-center gap-1 text-xs text-zinc-500 hover:text-indigo-700"
            >
              <X size={11} /> Replace
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-indigo-100 bg-indigo-50">
              <Upload size={20} className="text-indigo-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-900">Drop your resume here</p>
              <p className="mt-1 text-xs text-zinc-500">PDF or DOCX · Up to 5 MB</p>
            </div>
          </div>
        )}
      </div>
      {uploadError && (
        <div className="mb-5 flex items-start gap-2.5 rounded-[12px] border border-rose-200 bg-rose-50 p-3">
          <AlertCircle size={14} className="mt-0.5 flex-shrink-0 text-rose-600" />
          <p className="text-xs text-rose-900">{uploadError}</p>
        </div>
      )}

      {/* Preferences — values are inferred on upload from parsed résumé and saved server-side */}
      <div className="card p-5 mb-5">
        <div className="mb-4">
          <p className="text-sm font-medium text-zinc-900">Search preferences</p>
          <p className="mt-1 text-xs text-zinc-500">
            When you upload a résumé, we fill target role, seniority, and key skills from the parsed profile. Adjust
            anything here and click Save to persist edits.
          </p>
        </div>
        {loadingProfile ? (
          <div className="mb-4 flex items-center gap-2 text-xs text-zinc-500">
            <Loader2 size={12} className="animate-spin" />
            Loading saved preferences...
          </div>
        ) : null}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-600">Target role</label>
            <input className="field text-sm" value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. ML Engineer" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-600">Location</label>
            <input className="field text-sm" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Remote, London" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-600">Min salary (USD)</label>
            <input className="field text-sm" value={salary} onChange={(e) => setSalary(e.target.value)} placeholder="e.g. 140000" type="number" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-zinc-600">Seniority</label>
            <select
              className="field text-sm"
              value={seniority}
              onChange={(e) => setSeniority(e.target.value as UserPreferences['seniority'])}
            >
              {SENIORITY_OPTIONS.map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="col-span-2">
            <label className="mb-1.5 block text-xs font-medium text-zinc-600">Key skills</label>
            <input className="field text-sm" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="e.g. RAG, LLMs, Python" />
          </div>
        </div>
        {prefsStatus && (
          <div
            className={cn(
              'flex items-start gap-2 text-xs rounded-md px-3 py-2 mt-4',
              prefsStatus.type === 'success'
                ? 'border border-emerald-200 bg-emerald-50 text-emerald-900'
                : 'border border-rose-200 bg-rose-50 text-rose-900'
            )}
          >
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            <span>{prefsStatus.text}</span>
          </div>
        )}
        {!loadingProfile && !resumeExists && (
          <div className="mt-4 flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950">
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            <span>Upload a resume first to enable preference saving.</span>
          </div>
        )}
        <div className="mt-4 flex gap-2 border-t border-zinc-100 pt-4">
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
            <p className="text-sm font-medium text-zinc-900">AI profile analysis</p>
            <p className="mt-0.5 text-xs text-zinc-500">Get archetypes, skill gaps, and target companies</p>
          </div>
          <button
            onClick={() => analyzeWithAI()}
            disabled={analyzing || loadingProfile || !resumeExists}
            className="btn btn-primary text-xs gap-1.5"
          >
            {analyzing ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            {analyzing ? 'Analyzing…' : 'Analyze with AI'}
          </button>
        </div>

        <div
          className={cn(
            'min-h-[100px] rounded-[12px] border border-[#e7e8ee] bg-zinc-50 p-4 text-xs leading-relaxed text-zinc-800 whitespace-pre-wrap',
            !analysis && 'flex items-center justify-center text-zinc-500',
          )}
        >
          {analysis || (
            <div className="text-center">
              <FileText size={20} className="mx-auto mb-2 opacity-40" />
              <p>Upload your resume and click Analyze to see your profile breakdown</p>
            </div>
          )}
          {analyzing && <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-indigo-400 align-middle" />}
        </div>
      </div>
    </div>
  )
}
