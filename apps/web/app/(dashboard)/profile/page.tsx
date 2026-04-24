'use client'

import {
  Share2,
  Pencil,
  TrendingUp,
  Info,
  Upload,
  FileText,
  Code2,
  Plus,
  Eye,
  Hand,
  CheckCircle2,
  Circle,
} from 'lucide-react'

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-4 bg-[#f5faf8] px-4 py-4 dark:bg-transparent sm:px-6">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[32px] font-medium leading-[1.03] tracking-[-0.012em] text-[#171d1c] dark:text-slate-100">Your Professional Brand</h1>
          <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">Manage your presence and see how you rank in the current market.</p>
        </div>
        <div className="flex gap-2">
          <button className="inline-flex h-8 items-center gap-2 border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 px-4 text-[12px] font-medium text-[#171d1c] dark:text-slate-100">
            <Share2 size={14} />
            Share Profile
          </button>
          <button className="inline-flex h-8 items-center gap-2 border border-[0.5px] border-[#008378] bg-[#00685f] px-4 text-[12px] font-medium text-white">
            <Pencil size={14} />
            Edit Brand
          </button>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
        <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-3 md:col-span-8">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Market Insights</h2>
              <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">This shows how in-demand your current skills are.</p>
            </div>
            <div className="inline-flex items-center gap-2 bg-[#f0f5f2] px-3 py-1 text-[12px] font-medium text-[#00685f] dark:bg-slate-800 dark:text-teal-400">
              <TrendingUp size={14} />
              High Demand
            </div>
          </div>

          <div className="mb-4 border-l-[2px] border-[#D97706] bg-[#f0f5f2] p-3 dark:bg-slate-800/80">
            <div className="flex items-start gap-3">
              <Info size={16} className="mt-0.5 text-[#831ada]" />
              <div>
                <p className="text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">Optimization Suggestion</p>
                <p className="text-[13px] leading-[1.3] text-[#3d4947] dark:text-slate-400">
                  Your "Cloud Architecture" skills are currently peaking. Consider updating your primary resume headline to
                  reflect this expertise for 22% higher visibility.
                </p>
              </div>
            </div>
          </div>

          <div className="flex h-48 items-end gap-2 border-b border-[0.5px] border-[#dbe3e0] px-3 dark:border-slate-600">
            <div className="h-[30%] flex-1 bg-[#dee4e1] dark:bg-slate-700" />
            <div className="h-[45%] flex-1 bg-[#dee4e1] dark:bg-slate-700" />
            <div className="h-[85%] flex-1 bg-[#008378] dark:bg-teal-600" />
            <div className="h-[60%] flex-1 bg-[#dee4e1] dark:bg-slate-700" />
            <div className="h-[75%] flex-1 bg-[#dee4e1] dark:bg-slate-700" />
            <div className="h-[40%] flex-1 bg-[#dee4e1] dark:bg-slate-700" />
            <div className="h-[55%] flex-1 bg-[#dee4e1] dark:bg-slate-700" />
          </div>
          <div className="mt-2 flex justify-between px-3 text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">
            <span>JAN</span><span>MAR</span><span className="font-semibold text-[#00685f] dark:text-teal-400">CURRENT</span><span>JUL</span><span>SEP</span><span>NOV</span><span>PROJ</span>
          </div>
        </section>

        <aside className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-3 md:col-span-4">
          <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Profile Strength</h2>
          <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">92% Complete</p>
          <div className="my-5 flex justify-center">
            <div className="relative h-32 w-32">
              <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
                <circle cx="60" cy="60" r="52" fill="none" strokeWidth="8" className="stroke-[#e4e9e7] dark:stroke-slate-700" />
                <circle cx="60" cy="60" r="52" fill="none" strokeWidth="8" strokeDasharray="327" strokeDashoffset="26" className="stroke-[#00685f] dark:stroke-teal-400" />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[24px] font-semibold text-[#171d1c] dark:text-slate-100">92%</span>
            </div>
          </div>
          <div className="space-y-2 text-[13px]">
            <div className="flex items-center justify-between"><span className="inline-flex items-center gap-2"><CheckCircle2 size={14} className="text-[#00685f] dark:text-teal-400" />Verified Skills</span><span className="text-[#6d7a77] dark:text-slate-400">12/12</span></div>
            <div className="flex items-center justify-between"><span className="inline-flex items-center gap-2"><CheckCircle2 size={14} className="text-[#00685f] dark:text-teal-400" />Work History</span><span className="text-[#6d7a77] dark:text-slate-400">Complete</span></div>
            <div className="flex items-center justify-between"><span className="inline-flex items-center gap-2"><Circle size={14} className="text-[#6d7a77] dark:text-slate-400" />Video Intro</span><span className="text-[#00685f] dark:text-teal-400">Add +</span></div>
          </div>
        </aside>
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Manage Your Resumes</h2>
          <button className="inline-flex items-center gap-1 text-[12px] font-semibold text-[#00685f] dark:text-teal-400">
            <Upload size={14} />Upload New
          </button>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <article className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-3">
            <div className="mb-3 flex items-start gap-3">
              <div className="flex h-20 w-14 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.5)] bg-[#f0f5f2]"><FileText size={16} className="text-[#6d7a77] dark:text-slate-400" /></div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">Product_Lead_2024.pdf</p>
                <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">Updated 2 days ago</p>
                <span className="mt-2 inline-block bg-[#eaefed] px-2 py-1 text-[10px] leading-none">ATS-FRIENDLY</span>
              </div>
            </div>
            <div className="flex gap-3 border-t border-[0.5px] border-[#e4e9e7] pt-2 text-[13px]">
              <button className="text-[#00685f] dark:text-teal-400">View</button><button className="text-[#6d7a77] dark:text-slate-400">Analyze</button>
            </div>
          </article>

          <article className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-3">
            <div className="mb-3 flex items-start gap-3">
              <div className="flex h-20 w-14 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.5)] bg-[#f0f5f2]"><Code2 size={16} className="text-[#6d7a77] dark:text-slate-400" /></div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">Eng_Architecture_V2.pdf</p>
                <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">Updated 1 month ago</p>
                <span className="mt-2 inline-block bg-[#eaefed] px-2 py-1 text-[10px] leading-none">TECHNICAL</span>
              </div>
            </div>
            <div className="flex gap-3 border-t border-[0.5px] border-[#e4e9e7] pt-2 text-[13px]">
              <button className="text-[#00685f] dark:text-teal-400">View</button><button className="text-[#6d7a77] dark:text-slate-400">Analyze</button>
            </div>
          </article>

          <article className="flex flex-col items-center justify-center gap-2 border border-dashed border-[0.5px] border-[#bcc9c6] bg-white dark:bg-slate-900 p-3 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#eaefed]"><Plus size={16} className="text-[#00685f] dark:text-teal-400" /></div>
            <p className="text-[12px] font-semibold text-[#171d1c] dark:text-slate-100">Create Tailored Version</p>
            <p className="text-[13px] leading-[1.2] text-[#6d7a77] dark:text-slate-400">Generate a version for a specific job role.</p>
          </article>
        </div>
      </section>

      <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Your Key Skills</h2>
          <button className="text-[12px] font-semibold text-[#00685f] dark:text-teal-400">Manage All</button>
        </div>
        <div className="flex flex-wrap gap-2 text-[13px]">
          <span className="border border-[0.5px] border-teal-200 bg-teal-50 px-3 py-1.5 leading-none text-[#00685f] dark:border-teal-500/40 dark:bg-teal-950/40 dark:text-teal-300">Product Strategy</span>
          <span className="border border-[0.5px] border-teal-200 bg-teal-50 px-3 py-1.5 leading-none text-[#00685f] dark:border-teal-500/40 dark:bg-teal-950/40 dark:text-teal-300">React.js</span>
          <span className="border border-[0.5px] border-teal-200 bg-teal-50 px-3 py-1.5 leading-none text-[#00685f] dark:border-teal-500/40 dark:bg-teal-950/40 dark:text-teal-300">System Design</span>
          <span className="border border-[0.5px] border-[#bcc9c6] bg-[#f0f5f2] px-3 py-1.5 leading-none text-[#3d4947] dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">Agile Methodology</span>
          <span className="border border-[0.5px] border-[#bcc9c6] bg-[#f0f5f2] px-3 py-1.5 leading-none text-[#3d4947] dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">Cloud Infrastructure</span>
          <span className="border border-[0.5px] border-[#bcc9c6] bg-[#f0f5f2] px-3 py-1.5 leading-none text-[#3d4947] dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">User Research</span>
          <span className="border border-[0.5px] border-[#bcc9c6] bg-[#f0f5f2] px-3 py-1.5 leading-none text-[#3d4947] dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">Data Analysis</span>
          <span className="border border-dashed border-[0.5px] border-amber-400 px-3 py-1.5 leading-none text-amber-700 dark:border-amber-500/50 dark:text-amber-300">+ AI Prompt Engineering</span>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <h3 className="mb-4 text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Profile Visibility</h3>
          <div className="space-y-4 text-[13px]">
            <div className="flex items-center justify-between"><span className="inline-flex items-center gap-2"><Eye size={14} />Search Appearances</span><span className="text-[#171d1c] dark:text-slate-100">142</span></div>
            <div className="flex items-center justify-between"><span className="inline-flex items-center gap-2"><Hand size={14} />Profile Views</span><span className="text-[#171d1c] dark:text-slate-100">28</span></div>
          </div>
        </section>
        <section className="border border-[0.5px] border-[rgba(188,201,198,0.88)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <h3 className="mb-4 text-[24px] font-medium leading-[1.05] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Endorsements</h3>
          <p className="text-[13px] leading-[1.3] text-[#3d4947]">
            You've been endorsed for <span className="font-semibold text-[#171d1c] dark:text-slate-100">System Design</span> by 3 people from your previous company this week.
          </p>
        </section>
      </div>
    </div>
  )
}
