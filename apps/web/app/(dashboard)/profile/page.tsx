'use client'

import {
  Share2,
  Pencil,
  TrendingUp,
  Info,
  Upload,
  FileText,
  Plus,
  Eye,
  Loader2,
} from 'lucide-react'
import Link from 'next/link'
import { useMemo } from 'react'
import useSWR from 'swr'
import { useAuth } from '@clerk/nextjs'
import { useDashboard } from '@/hooks/useDashboard'
import { isE2EAuthBypass } from '@/lib/e2e'
import { resumeApi } from '@/lib/api'

export default function ProfilePage() {
  const { isLoaded, isSignedIn } = useAuth()
  const ready = isE2EAuthBypass() || (isLoaded && isSignedIn)
  const { summary, loading: dashLoading } = useDashboard()

  const { data: profile, error: resumeError, isLoading: resumeLoading } = useSWR(
    ready ? 'profile-resume' : null,
    async () => {
      const st = await resumeApi.onboardingStatus()
      if (st.state === 'no_resume') return null
      return resumeApi.get()
    },
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )

  const skillTags = useMemo(() => {
    const p = profile?.parsed_profile
    if (!p) return [] as string[]
    const list = (p.top_skills?.length ? p.top_skills : p.skills) ?? []
    return list.slice(0, 12)
  }, [profile])

  const views = summary?.profile_views

  return (
    <div className="mx-auto max-w-7xl space-y-4 bg-[#f5faf8] px-4 py-4 dark:bg-transparent sm:px-6">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[32px] font-medium leading-[1.03] tracking-[-0.012em] text-[#171d1c] dark:text-slate-100">
            Your professional brand
          </h1>
          <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">
            Pulled from your saved résumé and dashboard — no decorative scores.
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/resume"
            className="inline-flex h-8 items-center gap-2 border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white px-4 text-[12px] font-medium text-[#171d1c] dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          >
            <Upload size={14} />
            Résumé lab
          </Link>
          <Link
            href="/settings"
            className="inline-flex h-8 items-center gap-2 border border-[0.5px] border-[#008378] bg-[#00685f] px-4 text-[12px] font-medium text-white"
          >
            <Pencil size={14} />
            Settings
          </Link>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
        <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white p-3 dark:border-slate-700 dark:bg-slate-900 md:col-span-8">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">
                Parsed headline
              </h2>
              <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">From your latest résumé upload.</p>
            </div>
            {profile?.parsed_profile?.summary ? (
              <div className="inline-flex items-center gap-2 bg-[#f0f5f2] px-3 py-1 text-[12px] font-medium text-[#00685f] dark:bg-slate-800 dark:text-teal-400">
                <TrendingUp size={14} />
                Parsed
              </div>
            ) : null}
          </div>

          <div className="mb-4 border-l-[2px] border-[#D97706] bg-[#f0f5f2] p-3 dark:bg-slate-800/80">
            <div className="flex items-start gap-3">
              <Info size={16} className="mt-0.5 text-[#831ada]" />
              <div>
                <p className="text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">Summary</p>
                <p className="text-[13px] leading-[1.3] text-[#3d4947] dark:text-slate-400">
                  {resumeLoading || dashLoading ? (
                    <span className="inline-flex items-center gap-1">
                      <Loader2 className="animate-spin" size={14} /> Loading…
                    </span>
                  ) : resumeError ? (
                    'Could not load résumé profile.'
                  ) : profile?.parsed_profile?.summary?.trim() ? (
                    profile.parsed_profile.summary
                  ) : (
                    <>
                      No parser summary yet.{' '}
                      <Link href="/resume" className="font-semibold text-[#00685f] underline-offset-2 hover:underline">
                        Upload or refresh
                      </Link>{' '}
                      in Résumé lab.
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded border border-[0.5px] border-[#dbe3e0] bg-[#fafcfb] p-4 dark:border-slate-600">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#6d7a77]">Headline</p>
            <p className="mt-1 text-[15px] font-medium text-[#171d1c] dark:text-slate-100">
              {profile?.parsed_profile?.headline?.trim() || '—'}
            </p>
          </div>
        </section>

        <aside className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white p-3 dark:border-slate-700 dark:bg-slate-900 md:col-span-4">
          <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Dashboard</h2>
          <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">
            {views != null ? `${views} profile views (from API)` : 'Profile views not reported for this workspace yet.'}
          </p>
          <div className="my-5 space-y-2 text-[13px]">
            <div className="flex justify-between">
              <span className="text-[#6d7a77]">Pipeline</span>
              <span className="font-semibold text-[#171d1c] dark:text-slate-100">{summary?.pipeline_count ?? '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#6d7a77]">High-fit roles</span>
              <span className="font-semibold text-[#171d1c] dark:text-slate-100">{summary?.high_fit_count ?? '—'}</span>
            </div>
          </div>
          <Link href="/dashboard" className="text-[12px] font-semibold text-[#00685f] hover:underline dark:text-teal-400">
            Open overview →
          </Link>
        </aside>
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Your résumé file</h2>
          <Link
            href="/resume"
            className="inline-flex items-center gap-1 text-[12px] font-semibold text-[#00685f] dark:text-teal-400"
          >
            <Upload size={14} />
            Manage
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {profile ? (
            <article className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
              <div className="mb-3 flex items-start gap-3">
                <div className="flex h-20 w-14 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.5)] bg-[#f0f5f2]">
                  <FileText size={16} className="text-[#6d7a77] dark:text-slate-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">{profile.file_name}</p>
                  <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">v{profile.version}</p>
                  <span className="mt-2 inline-block bg-[#eaefed] px-2 py-1 text-[10px] leading-none dark:bg-slate-800">ON FILE</span>
                </div>
              </div>
              <div className="flex gap-3 border-t border-[0.5px] border-[#e4e9e7] pt-2 text-[13px] dark:border-slate-600">
                <Link href="/resume" className="text-[#00685f] dark:text-teal-400">
                  View in lab
                </Link>
              </div>
            </article>
          ) : (
            <article className="flex flex-col items-center justify-center gap-2 border border-dashed border-[0.5px] border-[#bcc9c6] bg-white p-6 text-center dark:border-slate-600 dark:bg-slate-900 md:col-span-2">
              <p className="text-[13px] text-[#6d7a77] dark:text-slate-400">No résumé on file. Upload one to power matching and drafts.</p>
              <Link
                href="/resume"
                className="inline-flex items-center gap-1 text-[12px] font-semibold text-[#00685f] dark:text-teal-400"
              >
                <Upload size={14} /> Go to Résumé lab
              </Link>
            </article>
          )}

          <article className="flex flex-col items-center justify-center gap-2 border border-dashed border-[0.5px] border-[#bcc9c6] bg-white p-3 text-center dark:border-slate-700 dark:bg-slate-900">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#eaefed]">
              <Plus size={16} className="text-[#00685f] dark:text-teal-400" />
            </div>
            <p className="text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">Tailored versions</p>
            <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">Use Approvals and drafts per application; multi-file versions are not stored separately here.</p>
          </article>
        </div>
      </section>

      <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Key skills (parsed)</h2>
          <Link href="/resume" className="text-[12px] font-semibold text-[#00685f] dark:text-teal-400">
            Edit preferences
          </Link>
        </div>
        <div className="flex flex-wrap gap-2 text-[13px]">
          {skillTags.length ? (
            skillTags.map((s) => (
              <span
                key={s}
                className="border border-[0.5px] border-teal-200 bg-teal-50 px-3 py-1.5 leading-none text-[#00685f] dark:border-teal-500/40 dark:bg-teal-950/40 dark:text-teal-300"
              >
                {s}
              </span>
            ))
          ) : (
            <p className="text-[13px] text-[#6d7a77] dark:text-slate-400">No parsed skills yet — upload a résumé or save preferences.</p>
          )}
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h3 className="mb-4 text-[20px] font-medium text-[#171d1c] dark:text-slate-100">Visibility</h3>
          <div className="space-y-3 text-[13px] text-[#3d4947] dark:text-slate-400">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2">
                <Eye size={14} /> Profile views (API)
              </span>
              <span className="font-semibold text-[#171d1c] dark:text-slate-100">{views ?? '—'}</span>
            </div>
            <p className="text-xs">Third-party endorsements are not synced in this build.</p>
          </div>
        </section>
        <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h3 className="mb-4 text-[20px] font-medium text-[#171d1c] dark:text-slate-100">Share</h3>
          <p className="text-[13px] leading-[1.3] text-[#3d4947] dark:text-slate-400">
            Public profile links are not enabled yet. Use Résumé lab and Discover with your signed-in account.
          </p>
          <button
            type="button"
            disabled
            className="mt-3 inline-flex items-center gap-2 text-[12px] font-semibold text-[#9ca3af]"
            title="Not available"
          >
            <Share2 size={14} />
            Share (soon)
          </button>
        </section>
      </div>
    </div>
  )
}
