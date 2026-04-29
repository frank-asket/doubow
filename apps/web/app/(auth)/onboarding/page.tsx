'use client'

import Link from 'next/link'
import type { Route } from 'next'
import { trackEvent } from '@/lib/telemetry'

const steps = [
  {
    title: 'Resume profile',
    body: 'Upload your resume so Doubow can build your profile and scoring context.',
    href: '/resume' as Route,
    cta: 'Open Resume',
  },
  {
    title: 'Discover opportunities',
    body: 'Review role matches and start building your pipeline from high-fit opportunities.',
    href: '/discover' as Route,
    cta: 'Open Discover',
  },
  {
    title: 'Reconnect integrations',
    body: 'Connect or reconnect Gmail and LinkedIn to support draft handoff workflows.',
    href: '/settings' as Route,
    cta: 'Open Settings',
  },
] as const

export default function OnboardingPage() {
  return (
    <main className="min-h-screen bg-[#f7f9fb] px-4 py-10 text-[#171d1c] sm:px-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="rounded-2xl border border-[#c6c6cd] bg-white p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[#00685f]">Getting Started</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.01em] text-[#000000]">Welcome to Doubow</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#3d4947]">
            Complete these setup steps to start receiving useful matches and managing your outreach workflow from one
            dashboard.
          </p>
        </header>

        <section className="space-y-3">
          {steps.map((step, idx) => (
            <article key={step.title} className="rounded-xl border border-[#c6c6cd] bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[#6d7a77]">Step {idx + 1}</p>
              <h2 className="mt-1 text-lg font-semibold text-[#000000]">{step.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3d4947]">{step.body}</p>
              <Link
                href={step.href}
                onClick={() =>
                  trackEvent('onboarding_step_clicked', {
                    step: idx + 1,
                    title: step.title,
                    destination: step.href,
                  })
                }
                className="mt-4 inline-flex h-9 items-center rounded-md border border-[#00685f] bg-[#00685f] px-4 text-sm font-medium text-white hover:bg-[#005049]"
              >
                {step.cta}
              </Link>
            </article>
          ))}
        </section>

        <footer className="pt-2">
          <Link
            href={'/dashboard' as Route}
            onClick={() => trackEvent('onboarding_skip_clicked', { destination: '/dashboard' })}
            className="inline-flex h-9 items-center rounded-md border border-[#c6c6cd] bg-white px-4 text-sm font-medium text-[#171d1c] hover:bg-[#f2f4f6]"
          >
            Skip to dashboard
          </Link>
        </footer>
      </div>
    </main>
  )
}
