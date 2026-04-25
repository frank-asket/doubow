'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import { Upload, CheckCircle, Loader2, Sparkles, X, AlertCircle, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useResumeUpload } from '@/hooks/useResumeUpload'
import { isE2EAuthBypass } from '@/lib/e2e'
import { ApiError, resumeApi } from '@/lib/api'
import { isMockApiEnabled } from '@/lib/mock-api'
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

  const extractedSkills = skills
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 8)

  return (
    <div className="resume-lab mx-auto max-w-7xl space-y-3 bg-[#f5faf8] dark:bg-transparent px-4 pb-4 pt-2 sm:px-6 sm:pt-3 md:space-y-4">
      {isMockApiEnabled() ? (
        <div
          role="status"
          className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2.5 text-xs leading-relaxed text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-50"
        >
          Demo API mode is on: this page loads in-memory fixtures (e.g. sample name and CV filename), not data from
          your real backend. For production, unset{' '}
          <code className="rounded bg-amber-100/90 px-1 font-mono text-[11px] dark:bg-amber-900/60">NEXT_PUBLIC_USE_MOCK_API</code>{' '}
          in Vercel and set{' '}
          <code className="rounded bg-amber-100/90 px-1 font-mono text-[11px] dark:bg-amber-900/60">NEXT_PUBLIC_API_URL</code>{' '}
          to your API.
        </div>
      ) : null}

      <section className="flex flex-wrap items-end justify-between gap-3 border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 pb-[11px]">
        <div>
          <h1 className="hidden md:block text-[30px] font-medium leading-[1.05] tracking-[-0.012em] text-[#171d1c] dark:text-slate-100">Resume Lab</h1>
          <p className="text-[13px] text-[#6d7a77] dark:text-slate-400">Manage iterations, extract technical metadata, and align with market sectors.</p>
        </div>
        <div className="flex gap-2">
          <button
            className="h-[31px] border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 px-4 text-[12px] font-medium uppercase tracking-[0.05em] text-[#171d1c] dark:text-slate-100"
            onClick={() => fileRef.current?.click()}
          >
            Replace Resume
          </button>
          <button
            className="inline-flex h-[31px] items-center gap-1 border border-[0.5px] border-[#008378] bg-[#00685f] px-4 text-[12px] font-medium uppercase tracking-[0.05em] text-white disabled:opacity-70"
            onClick={() => analyzeWithAI()}
            disabled={analyzing || loadingProfile || !resumeExists}
          >
            {analyzing ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            Analyze Core
          </button>
        </div>
      </section>

      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) handleFile(f)
        }}
      />

      {uploadError && (
        <div className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
          <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <section className="space-y-4 lg:col-span-8">
          <article className="md:hidden border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 p-3">
            <button
              className="inline-flex h-11 w-full items-center justify-center gap-2 border border-[0.5px] border-[#008378] bg-[#00685f] text-[20px] font-medium text-white tracking-[-0.01em]"
              onClick={() => fileRef.current?.click()}
            >
              <Upload size={16} />
              Upload New Resume
            </button>
          </article>

          <article
            className={cn(
              'relative cursor-pointer border border-[0.5px] bg-white dark:bg-slate-900 p-4 transition-colors',
              (dragOver || uploaded) && 'bg-teal-50/40',
            )}
            style={{ borderColor: dragOver || uploaded ? '#67d7cb' : 'rgba(188, 201, 198, 0.92)' }}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
          >
            <div className="absolute left-0 top-4 h-10 w-1 bg-[#D97706]" />
            <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-center gap-3 pl-1">
                <div className="flex h-16 w-12 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-[#f0f5f2]">
                  <FileText size={18} className="text-[#6d7a77] dark:text-slate-400" />
                </div>
                <div className="min-w-0">
                  <h3 className="truncate text-[16px] font-medium uppercase leading-[1.08] text-[#171d1c] dark:text-slate-100">{fileName || 'Resume_Not_Uploaded.pdf'}</h3>
                  <p className="mt-0.5 text-[11px] uppercase leading-[1.08] tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">
                    {uploaded ? 'UPLOADED: JUST NOW' : 'UPLOAD A RESUME TO START EXTRACTION'}
                  </p>
                  {uploading ? (
                    <p className="mt-2 inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.08em] text-[#00685f]">
                      <Loader2 size={11} className="animate-spin" /> Uploading...
                    </p>
                  ) : uploaded ? (
                    <div className="mt-2 inline-flex h-5 items-center gap-1 bg-teal-50 px-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f] border border-[0.5px] border-teal-200">
                      <CheckCircle size={10} /> AI Scanned
                    </div>
                  ) : (
                    <div className="mt-2 inline-flex h-5 items-center gap-1 bg-[#f0f5f2] px-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400 border border-[0.5px] border-[rgba(188,201,198,0.92)]">
                      <Upload size={10} /> Drop PDF or DOCX
                    </div>
                  )}
                </div>
              </div>
              <div className="text-right">
                <p className="text-[52px] leading-[0.92] font-black tracking-[-0.03em] text-[#00685f]">{uploaded ? '94.2%' : '--'}</p>
                <p className="text-[11px] uppercase tracking-[0.08em] leading-none text-[#6d7a77] dark:text-slate-400">Match Score</p>
              </div>
            </div>

            <div className="grid grid-cols-1 border-t border-[0.5px] border-[rgba(188,201,198,0.88)] sm:grid-cols-3">
              {[
                ['Tokens Identified', uploaded ? '1,402' : '0', uploaded ? 85 : 0],
                ['Confidence Level', uploaded ? 'High (0.98)' : '--', uploaded ? 98 : 0],
                ['Processing Time', uploaded ? '1.4s' : '--', uploaded ? 40 : 0],
              ].map(([label, value, pct], idx) => (
                <div key={label} className={cn('px-3.5 py-[11px]', idx < 2 && 'sm:border-r sm:border-[0.5px] sm:border-[rgba(188,201,198,0.88)]')}>
                  <p className="text-[11px] uppercase leading-none tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">{label}</p>
                  <p className="mt-0.5 text-[16px] font-medium leading-[1.08] text-[#171d1c] dark:text-slate-100">{value}</p>
                  <div className="mt-2 h-1 bg-[#eaefed]">
                    <div className="h-full bg-[#00685f]" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {uploaded ? (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setUploaded(false)
                  setFileName('')
                }}
                className="mt-3 inline-flex items-center gap-1 text-[11px] text-[#6d7a77] dark:text-slate-400 hover:text-[#00685f]"
              >
                <X size={11} /> Replace file
              </button>
            ) : null}
          </article>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <article className="border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 p-3.5">
              <div className="mb-3 flex items-center justify-between">
                <h4 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Extracted Keywords</h4>
                <span className="material-symbols-outlined text-[#00685f]">data_object</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(extractedSkills.length ? extractedSkills : ['React', 'Node', 'Kubernetes', 'AWS']).map((skill) => (
                  <span key={skill} className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-[#eaefed] px-2 py-px text-[10px] uppercase leading-none tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
                    {skill}
                  </span>
                ))}
              </div>
            </article>

            <article className="border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 p-3.5">
              <div className="mb-3 flex items-center justify-between">
                <h4 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Market Alignment</h4>
                <span className="material-symbols-outlined text-[#00685f]">trending_up</span>
              </div>
              <div className="space-y-3">
                {[
                  ['FinTech', 98],
                  ['SaaS/Enterprise', 82],
                ].map(([label, pct]) => (
                  <div key={label}>
                    <div className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
                      <span>{label}</span>
                      <span className="font-semibold text-[#00685f]">{pct}%</span>
                    </div>
                    <div className="h-1 bg-[#eaefed]">
                      <div className="h-full bg-[#00685f]" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <article className="hidden border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 md:block">
            <header className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-slate-50/50 px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-2 text-[12px] font-semibold uppercase tracking-[0.1em] text-[#171d1c] dark:text-slate-100">
                  <span className="material-symbols-outlined text-[16px] text-[#00685f]">history</span>
                  Version_Manifest
                </span>
                <span className="text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">8 Active Instances</span>
              </div>
            </header>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-slate-50/40 text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">
                    <th className="px-3 py-2">Tag</th>
                    <th className="px-3 py-2">Created_At</th>
                    <th className="px-3 py-2">Alignment</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="text-[13px]">
                  <tr className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700">
                    <td className="px-3 py-1.5 font-mono text-[#316bf3]">v4.2.1-SWE-L6</td>
                    <td className="px-3 py-1.5 text-[#6d7a77] dark:text-slate-400">2023-11-24 14:22</td>
                    <td className="px-3 py-1.5">
                      <div className="inline-flex items-center gap-2">
                        <div className="h-1 w-20 bg-[#eaefed]"><div className="h-full w-[94%] bg-[#06b6a7]" /></div>
                        <span className="text-[12px] font-medium text-[#171d1c] dark:text-slate-100">94%</span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5"><span className="border border-[0.5px] border-teal-200 bg-teal-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f]">Production</span></td>
                    <td className="px-3 py-1.5 text-right text-[#00685f]">View</td>
                  </tr>
                  <tr className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700">
                    <td className="px-3 py-1.5 font-mono text-[#316bf3]">v4.1.0-ML-ENG</td>
                    <td className="px-3 py-1.5 text-[#6d7a77] dark:text-slate-400">2023-11-22 09:10</td>
                    <td className="px-3 py-1.5">
                      <div className="inline-flex items-center gap-2">
                        <div className="h-1 w-20 bg-[#eaefed]"><div className="h-full w-[78%] bg-amber-500" /></div>
                        <span className="text-[12px] font-medium text-[#171d1c] dark:text-slate-100">78%</span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5"><span className="border border-[0.5px] border-slate-200 bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Archived</span></td>
                    <td className="px-3 py-1.5 text-right text-[#00685f]">View</td>
                  </tr>
                  <tr className="bg-amber-50/40">
                    <td className="px-3 py-1.5 font-mono text-[#316bf3]">v4.3.0-DRAFT</td>
                    <td className="px-3 py-1.5 text-[#6d7a77] dark:text-slate-400">JUST NOW</td>
                    <td className="px-3 py-1.5 text-[12px] font-medium italic text-amber-700">CALCULATING...</td>
                    <td className="px-3 py-1.5 text-[11px] uppercase tracking-[0.08em] text-amber-700">HITL REQUIRED</td>
                    <td className="px-3 py-1.5 text-right"><button className="h-7 bg-amber-600 px-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-white">Reconcile</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </section>

        <aside className="space-y-4 lg:col-span-4">
          <article className="border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900">
            <header className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-slate-50 px-3 py-2">
              <h4 className="text-[12px] font-semibold uppercase tracking-[0.1em] text-[#171d1c] dark:text-slate-100">History Logs</h4>
            </header>
            <div>
              {[
                ['Resume_Standard_v3', '2023-09-12 • MATCH: 88%'],
                ['Creative_Portfolio_v2', '2023-08-05 • MATCH: 72%'],
                ['Resume_Legacy_Base', '2023-01-20 • MATCH: 61%'],
              ].map(([title, meta]) => (
                <div key={title} className="flex items-center justify-between border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 px-3 py-3 last:border-b-0">
                  <div>
                    <p className="text-[13px] font-medium text-[#171d1c] dark:text-slate-100">{title}</p>
                    <p className="text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">{meta}</p>
                  </div>
                  <button className="material-symbols-outlined text-[#6d7a77] dark:text-slate-400">download</button>
                </div>
              ))}
            </div>
          </article>

          <article className="relative overflow-hidden border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-amber-50 p-3">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#D97706]" />
            <h5 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#92400e]">Human Intervention Required</h5>
            <p className="mt-1 text-[12px] text-[#3d4947] dark:text-slate-400">
              Three experience gaps detected in period 2021-2022. Manual verification recommended before export.
            </p>
            <button className="mt-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#92400e] underline">Fix discrepancy</button>
          </article>

          <article className="border border-[0.5px] border-[#008378] bg-[#00685f] p-3 text-white">
            <p className="text-[12px] font-semibold uppercase tracking-[0.08em]">Verified Status</p>
            <p className="mt-1 text-[12px] text-teal-100">This resume has been cryptographically signed.</p>
          </article>
        </aside>
      </div>

      <section className="border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900">
        <header className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-[#e4e9e7] px-3 py-2">
          <h4 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Operation Log</h4>
        </header>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-[12px]">
            <thead>
              <tr className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700 text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">
                <th className="px-3 py-2">Operation ID</th>
                <th className="px-3 py-2">Engine Module</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[0.5px] border-[#bcc9c6] dark:border-slate-700">
                <td className="px-3 py-2 font-mono text-[11px]">#RN-9821-X</td>
                <td className="px-3 py-2 font-mono text-[11px]">NER_ENTITY_EXTRACTOR</td>
                <td className="px-3 py-2">
                  <span className="border border-[0.5px] border-teal-200 bg-teal-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f]">Complete</span>
                </td>
                <td className="px-3 py-2 font-mono text-[11px]">14:30:12</td>
              </tr>
              <tr>
                <td className="px-3 py-2 font-mono text-[11px]">#RN-9820-A</td>
                <td className="px-3 py-2 font-mono text-[11px]">SEMANTIC_SIMILARITY_V2</td>
                <td className="px-3 py-2">
                  <span className="border border-[0.5px] border-teal-200 bg-teal-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f]">Complete</span>
                </td>
                <td className="px-3 py-2 font-mono text-[11px]">14:29:58</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
        <div className="mb-3">
          <h4 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Search Preferences</h4>
          <p className="mt-1 text-[12px] text-[#6d7a77] dark:text-slate-400">Review extracted preferences, tweak, and save.</p>
        </div>
        {loadingProfile ? (
          <p className="mb-3 inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">
            <Loader2 size={11} className="animate-spin" /> Loading saved preferences...
          </p>
        ) : null}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Target role</label>
            <input className="h-9 w-full border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 px-2 text-sm outline-none focus:border-[#00685f]" value={role} onChange={(e) => setRole(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Location</label>
            <input className="h-9 w-full border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 px-2 text-sm outline-none focus:border-[#00685f]" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Min salary (USD)</label>
            <input className="h-9 w-full border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 px-2 text-sm outline-none focus:border-[#00685f]" value={salary} type="number" onChange={(e) => setSalary(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Seniority</label>
            <select className="h-9 w-full border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 px-2 text-sm outline-none focus:border-[#00685f]" value={seniority} onChange={(e) => setSeniority(e.target.value as UserPreferences['seniority'])}>
              {SENIORITY_OPTIONS.map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="col-span-2">
            <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Key skills</label>
            <input className="h-9 w-full border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 px-2 text-sm outline-none focus:border-[#00685f]" value={skills} onChange={(e) => setSkills(e.target.value)} />
          </div>
        </div>
        {prefsStatus && (
          <div
            className={cn(
              'mt-3 flex items-start gap-2 px-3 py-2 text-xs',
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
          <div className="mt-3 flex items-start gap-2 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950">
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            <span>Upload a resume first to enable preference saving.</span>
          </div>
        )}
        <div className="mt-3 flex gap-2 border-t border-[0.5px] border-[#bcc9c6] dark:border-slate-700 pt-3">
          <button
            onClick={() => savePreferences()}
            disabled={savingPrefs || loadingProfile || !resumeExists}
            className="inline-flex h-8 items-center gap-1 border border-[0.5px] border-[#008378] bg-[#00685f] px-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-white disabled:opacity-70"
          >
            {savingPrefs ? <Loader2 size={12} className="animate-spin" /> : null}
            {savingPrefs ? 'Saving...' : 'Save Preferences'}
          </button>
          <button
            onClick={() => {
              hydrateFromPrefs(savedPrefs)
              setPrefsStatus(null)
            }}
            disabled={savingPrefs || loadingProfile}
            className="inline-flex h-8 items-center border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[#171d1c] dark:text-slate-100"
          >
            Reset
          </button>
        </div>
        <div className="mt-3 min-h-[90px] border border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-[#f0f5f2] p-3 text-xs leading-relaxed text-[#171d1c] dark:text-slate-100 whitespace-pre-wrap">
          {analysis || 'Run Analyze Core to generate AI extraction insights and role alignment recommendations.'}
          {analyzing && <span className="ml-1 inline-block h-3 w-0.5 animate-pulse bg-[#00685f] align-middle" />}
        </div>
      </section>

      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-[0.5px] border-[#bcc9c6] dark:border-slate-700 bg-white dark:bg-slate-900 md:hidden">
        <div className="mx-auto grid max-w-md grid-cols-4">
          {[
            { icon: 'edit_note', label: 'Editor', active: true },
            { icon: 'history', label: 'History', active: false },
            { icon: 'query_stats', label: 'Market', active: false },
            { icon: 'person', label: 'Profile', active: false },
          ].map(({ icon, label, active }) => (
            <button
              key={label}
              className={cn(
                'flex h-14 flex-col items-center justify-center gap-0.5 border-t-2 text-[10px] font-medium uppercase tracking-[0.08em]',
                active ? 'border-t-[#00685f] text-[#00685f]' : 'border-t-transparent text-[#6d7a77] dark:text-slate-400',
              )}
            >
              <span className="material-symbols-outlined text-[18px]">{icon}</span>
              {label}
            </button>
          ))}
        </div>
      </nav>
      <style jsx global>{`
        .resume-lab .material-symbols-outlined {
          font-family: 'Material Symbols Outlined';
          font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 20;
          line-height: 1;
          vertical-align: middle;
        }
      `}</style>
    </div>
  )
}
