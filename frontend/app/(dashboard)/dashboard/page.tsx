'use client'

import { CalendarDays, ChevronRight, Ellipsis, Plus, SearchCheck } from 'lucide-react'
import Link from 'next/link'
import { useDashboard } from '@/hooks/useDashboard'

export default function DashboardOverviewPage() {
  const { summary } = useDashboard()
  const totalApplied = summary?.pipeline_count ?? 0
  const interviewed = summary?.pending_approvals ?? 0
  const highFit = summary?.high_fit_count ?? 0

  return (
    <div className="space-y-5 p-5 sm:p-7">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-[34px] font-semibold leading-none tracking-[-0.02em] text-zinc-900 sm:text-[42px]">Dashboard</h1>
          <p className="mt-2 max-w-[22ch] text-[15px] text-zinc-500 sm:max-w-none">Take&apos;s a look at your monthly job search application.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-[10px] border border-[#e4e5ec] bg-white px-3 py-2 text-[14px] font-medium text-zinc-700 shadow-sm">
          <CalendarDays size={15} />
          This Month
        </button>
      </header>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <article className="rounded-[16px] border border-[#e7e8ee] bg-[radial-gradient(circle_at_top_left,_#efefff,_#f9f9ff_45%,_#ffffff)] p-6">
          <div className="flex items-center gap-5">
            <div className="space-y-2">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white shadow-sm">
                <SearchCheck size={18} />
              </span>
              <p className="text-[56px] font-semibold leading-none tracking-[-0.02em] text-zinc-900">{totalApplied}</p>
              <p className="text-[15px] text-zinc-500">Total Job Applied</p>
            </div>
            <div className="space-y-2">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-amber-200 text-amber-700 shadow-sm">
                <Plus size={18} />
              </span>
              <p className="text-[56px] font-semibold leading-none tracking-[-0.02em] text-zinc-900">{interviewed}</p>
              <p className="text-[15px] text-zinc-500">Interviewed</p>
            </div>
          </div>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <h2 className="text-[38px] font-semibold leading-none tracking-[-0.02em] text-zinc-900">Job Applied</h2>
          <div className="mt-4 flex items-center gap-5">
            <div
              className="h-[104px] w-[104px] rounded-full"
              style={{
                background:
                  'conic-gradient(#2f45ce 0deg 102deg, #eef0f5 102deg 258deg, #4f63db 258deg 360deg)',
              }}
            >
              <div className="m-[14px] h-[76px] w-[76px] rounded-full bg-white" />
            </div>
            <div className="space-y-2 text-[14px] text-zinc-500">
              <p>
                <span className="mr-2 inline-block h-2 w-2 rounded-full bg-zinc-300" />
                70% Unsuitable
              </p>
              <p>
                <span className="mr-2 inline-block h-2 w-2 rounded-full bg-indigo-600" />
                30% Interviewed
              </p>
            </div>
          </div>
          <Link href="/pipeline" className="mt-5 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700">
            View All Job Applied <ChevronRight size={14} />
          </Link>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-[38px] font-semibold leading-none tracking-[-0.02em] text-zinc-900">Upcoming Interview</h2>
            <span className="text-[14px] text-zinc-500">Today</span>
          </div>
          <p className="mt-2 text-[14px] text-zinc-500">Your next interview window</p>
          <div className="mt-4 rounded-[12px] border border-indigo-200 bg-indigo-50/50 p-3">
            <p className="text-[14px] font-semibold text-zinc-800">Senior Product Designer</p>
            <p className="mt-1 text-[12px] text-zinc-500">DigitalOcean · 10:00 - 11:00</p>
          </div>
          <Link href="/prep" className="mt-5 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700">
            View Schedule <ChevronRight size={14} />
          </Link>
        </article>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-[36px] font-semibold leading-none tracking-[-0.02em] text-zinc-900">Recent Applications History</h3>
            <Ellipsis size={18} className="text-zinc-400" />
          </div>
          <div className="space-y-4">
            {[
              { role: '3D Artist - Performance Marketing', company: 'Revolut', status: 'In Review' },
              { role: 'Software Engineer (Front-End)', company: 'Recurrency', status: 'Declined' },
              { role: 'Senior Digital Designer', company: 'Digital Ocean', status: 'Declined' },
            ].map((item) => (
              <div key={item.role} className="flex items-center justify-between border-b border-zinc-200/70 pb-3 last:border-0">
                <div>
                  <p className="text-[15px] font-semibold text-zinc-800">{item.role}</p>
                  <p className="text-[12px] text-zinc-500">{item.company}</p>
                </div>
                <span className="rounded-full bg-zinc-100 px-2 py-1 text-[12px] text-zinc-600">{item.status}</span>
              </div>
            ))}
          </div>
          <Link href="/pipeline" className="mt-4 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700">
            View All Applications History <ChevronRight size={14} />
          </Link>
        </article>

        <article className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-[36px] font-semibold leading-none tracking-[-0.02em] text-zinc-900">Saved jobs</h3>
            <Ellipsis size={18} className="text-zinc-400" />
          </div>
          <div className="space-y-4">
            {[
              'Senior IT Operations Engineer',
              'Creative Director - Crypto',
              'UX Researcher',
              'Full-Stack JavaScript Developer',
            ].map((title, idx) => (
              <div key={title} className="flex items-center justify-between border-b border-zinc-200/70 pb-3 last:border-0">
                <p className="text-[15px] font-semibold text-zinc-800">{title}</p>
                <span className="text-[12px] text-rose-500">{idx + 2} day to apply</span>
              </div>
            ))}
          </div>
          <Link href="/discover" className="mt-4 inline-flex items-center gap-1 text-[14px] font-semibold text-indigo-700">
            View Saved Jobs <ChevronRight size={14} />
          </Link>
        </article>
      </section>

      <section className="rounded-[14px] border border-indigo-100 bg-indigo-50/70 p-4">
        <p className="text-[14px] text-indigo-900">
          High-fit opportunities in your queue: <span className="font-semibold">{highFit}</span>
        </p>
      </section>
    </div>
  )
}
