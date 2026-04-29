'use client'

/** Visual layout aligned with `docs/mockup/subscription_billing/code.html` (Doubow branding + dashboard shell). */

import { useMemo } from 'react'
import {
  Sparkles,
  LineChart,
  BellRing,
  Brain,
  Scale,
  AlertTriangle,
  ChevronRight,
  Download,
} from 'lucide-react'
import { useUser } from '@clerk/nextjs'
import {
  isPaidPublicMetadata,
  planLabelFromPublicMetadata,
  type ClerkPlanPublicMetadata,
} from '@/lib/clerkPlan'
import { cn } from '@/lib/utils'

const INVOICE_ROWS = [
  { date: 'Oct 12, 2023', id: 'INV-88219', amount: '$0.00', status: 'Paid' as const },
  { date: 'Sep 12, 2023', id: 'INV-87442', amount: '$0.00', status: 'Paid' as const },
]

const FEATURES = [
  {
    icon: LineChart,
    title: 'Unlimited AI Job Scoring',
    body: 'Instant match analysis for every role you discover.',
  },
  {
    icon: BellRing,
    title: 'Priority Monitoring',
    body: 'Real-time alerts when top employers post new roles.',
  },
  {
    icon: Brain,
    title: 'Unlimited STAR Prep',
    body: 'Deep-dive interview coaching for situational questions.',
  },
  {
    icon: Scale,
    title: 'Negotiation Analytics',
    body: 'Live market data to maximize your offer potential.',
  },
] as const

export default function BillingPage() {
  const { user, isLoaded } = useUser()
  const meta = user?.publicMetadata as ClerkPlanPublicMetadata | undefined

  const planLabel = useMemo(() => planLabelFromPublicMetadata(meta), [meta])
  const isPaid = useMemo(() => isPaidPublicMetadata(meta), [meta])

  const tierTitle = planLabel === 'Free' ? 'Free Tier' : `${planLabel} Plan`
  const tierSubtitle = isPaid
    ? 'Full analytical suite — thank you for supporting Doubow.'
    : 'Limited analytical access'

  const creditsUsed = isPaid ? 5 : 3
  const creditsCap = 5
  const creditsPct = Math.min(100, Math.round((creditsUsed / creditsCap) * 100))

  const checkoutUrl =
    typeof process.env.NEXT_PUBLIC_BILLING_CHECKOUT_URL === 'string'
      ? process.env.NEXT_PUBLIC_BILLING_CHECKOUT_URL.trim()
      : ''
  const portalUrl =
    typeof process.env.NEXT_PUBLIC_BILLING_PORTAL_URL === 'string'
      ? process.env.NEXT_PUBLIC_BILLING_PORTAL_URL.trim()
      : ''

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <header className="mb-8">
        <h1 className="text-xl font-medium leading-tight tracking-[-0.01em] text-[#171d1c] dark:text-white">
          Subscription &amp; Billing
        </h1>
        <p className="mt-1 text-[13px] leading-relaxed text-[#3d4947] dark:text-slate-300">
          Manage your precision career tools and billing preferences.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:gap-4">
        {/* Left column */}
        <div className="space-y-4 lg:col-span-4">
          <div className="border border-[0.5px] border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-[12px] font-medium uppercase tracking-wider text-[#3d4947] dark:text-slate-300">
                Current Plan
              </span>
              <span className="border border-[0.5px] border-[#bcc9c6] bg-[#eaefed] px-2 py-0.5 text-[10px] font-medium uppercase text-[#3d4947] dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {isLoaded ? 'Active' : '…'}
              </span>
            </div>
            <div className="mb-6">
              <h2 className="text-base font-medium leading-tight tracking-[-0.01em] text-[#171d1c] dark:text-white">
                {!isLoaded ? '…' : tierTitle}
              </h2>
              <p className="mt-1 text-[13px] leading-snug text-[#3d4947] dark:text-slate-300">{tierSubtitle}</p>
            </div>
            <div className="space-y-3 border-t border-[0.5px] border-slate-100 pt-4 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-tight text-slate-500 dark:text-slate-300">
                  AI Credits
                </span>
                <span className="text-[11px] font-medium text-[#171d1c] dark:text-slate-200">
                  {creditsUsed} / {creditsCap} Monthly
                </span>
              </div>
              <div className="h-1 w-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full bg-teal-500 transition-[width]"
                  style={{ width: `${creditsPct}%` }}
                />
              </div>
            </div>
          </div>

          {!isPaid ? (
            <div className="border border-[0.5px] border-slate-200 border-l-[3px] border-l-amber-500 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 flex-shrink-0 text-amber-600" aria-hidden />
                <div>
                  <h3 className="text-[13px] font-semibold text-[#171d1c] dark:text-white">
                    Action Required
                  </h3>
                  <p className="mt-0.5 text-[12px] leading-tight text-[#3d4947] dark:text-slate-300">
                    No primary payment method detected. Add a card when you upgrade to prevent service
                    interruption.
                  </p>
                  {checkoutUrl ? (
                    <a
                      href={checkoutUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-block text-[11px] font-bold uppercase tracking-wider text-teal-600 hover:underline dark:text-teal-400"
                    >
                      Add Payment Method
                    </a>
                  ) : (
                    <span className="mt-3 block text-[11px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                      Add Payment Method
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="border border-[0.5px] border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <p className="text-[12px] font-semibold text-[#171d1c] dark:text-white">Billing</p>
              <p className="mt-1 text-[12px] text-[#3d4947] dark:text-slate-300">
                Update payment method or cancel from your billing provider.
              </p>
              {portalUrl ? (
                <a
                  href={portalUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-block text-[11px] font-bold uppercase tracking-wider text-teal-600 hover:underline dark:text-teal-400"
                >
                  Manage subscription
                </a>
              ) : (
                <p className="mt-3 text-[11px] text-slate-500 dark:text-slate-500">
                  Set <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">NEXT_PUBLIC_BILLING_PORTAL_URL</code>{' '}
                  for a self-serve portal link.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-4 lg:col-span-8">
          <div className="overflow-hidden border border-[0.5px] border-teal-600/30 bg-white dark:border-teal-500/30 dark:bg-slate-900">
            <div className="p-6">
              <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
                <div>
                  <div className="mb-1 flex items-center gap-2">
                    <Sparkles className="h-6 w-6 text-teal-600 dark:text-teal-400" aria-hidden />
                    <h2 className="text-xl font-medium leading-tight tracking-[-0.01em] text-[#171d1c] dark:text-white">
                      {isPaid ? 'Doubow Pro' : 'Upgrade to Pro'}
                    </h2>
                  </div>
                  <p className="text-[14px] leading-relaxed text-[#3d4947] dark:text-slate-300">
                    {isPaid
                      ? 'Your subscription is active — here is what you have access to.'
                      : 'Unlock the full analytical suite for high-performance job seeking.'}
                  </p>
                </div>
                {!isPaid ? (
                  <div className="text-right md:pl-4">
                    <div className="text-[28px] font-bold text-slate-900 dark:text-white">
                      €12<span className="text-sm font-normal text-slate-500 dark:text-slate-300">/month</span>
                    </div>
                    <div className="text-[11px] font-medium uppercase tracking-wider text-teal-600 dark:text-teal-400">
                      Billed Monthly
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2">
                {FEATURES.map(({ icon: Icon, title, body }) => (
                  <div key={title} className="flex gap-3">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center border border-[0.5px] border-teal-100 bg-teal-50 dark:border-teal-500/30 dark:bg-teal-950/40">
                      <Icon className="h-[18px] w-[18px] text-teal-600 dark:text-teal-400" aria-hidden />
                    </div>
                    <div>
                      <h4 className="text-[14px] font-semibold text-[#171d1c] dark:text-white">{title}</h4>
                      <p className="mt-0.5 text-[12px] text-[#3d4947] dark:text-slate-300">{body}</p>
                    </div>
                  </div>
                ))}
              </div>

              {!isPaid ? (
                <>
                  <div className="flex flex-col items-center gap-4 border-t border-[0.5px] border-slate-100 pt-6 dark:border-slate-700 sm:flex-row">
                    {checkoutUrl ? (
                      <a
                        href={checkoutUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full border border-[0.5px] border-teal-700 bg-teal-600 px-8 py-3 text-center text-[14px] font-semibold text-white transition-colors hover:bg-teal-700 sm:w-auto"
                      >
                        Start Free Trial
                      </a>
                    ) : (
                      <button
                        type="button"
                        disabled
                        title="Set NEXT_PUBLIC_BILLING_CHECKOUT_URL to enable checkout"
                        className="w-full cursor-not-allowed border border-[0.5px] border-slate-300 bg-slate-200 px-8 py-3 text-[14px] font-semibold text-slate-500 sm:w-auto dark:border-slate-600 dark:bg-slate-800 dark:text-slate-500"
                      >
                        Start Free Trial
                      </button>
                    )}
                    <p className="text-center text-[11px] text-slate-500 dark:text-slate-300 sm:text-left">
                      No credit card required for first 7 days. Cancel anytime.
                    </p>
                  </div>
                  {!checkoutUrl ? (
                    <p className="mt-4 text-[11px] text-amber-800 dark:text-amber-200/90">
                      Developer: set{' '}
                      <code className="rounded bg-amber-100 px-1 dark:bg-amber-950/80">NEXT_PUBLIC_BILLING_CHECKOUT_URL</code>{' '}
                      for Clerk Billing or Stripe Checkout.
                    </p>
                  ) : null}
                </>
              ) : (
                <p className="border-t border-[0.5px] border-slate-100 pt-6 text-[14px] font-medium text-teal-700 dark:border-slate-700 dark:text-teal-300">
                  Thank you for supporting Doubow.
                </p>
              )}
            </div>

            <div className="flex items-center justify-between bg-slate-900 px-6 py-4">
              <div className="flex min-w-0 items-center gap-3">
                <div className="h-2 w-2 flex-shrink-0 animate-pulse rounded-full bg-teal-400" />
                <span className="text-[12px] font-medium text-white">
                  {isPaid
                    ? 'Refer a friend — share Doubow with your network.'
                    : 'Early Adopter Discount: 20% off yearly plans applied at checkout.'}
                </span>
              </div>
              <ChevronRight className="h-5 w-5 flex-shrink-0 text-white/50" aria-hidden />
            </div>
          </div>

          <div className="border border-[0.5px] border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
            <div className="border-b border-[0.5px] border-slate-100 bg-slate-50/50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800/50">
              <h3 className="text-[12px] font-medium uppercase tracking-wider text-[#3d4947] dark:text-slate-300">
                Recent Invoices
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="border-b border-[0.5px] border-slate-100 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
                  <tr>
                    {['Date', 'Invoice #', 'Amount', 'Status', ''].map((h) => (
                      <th
                        key={h || 'dl'}
                        className={cn(
                          'px-4 py-2 text-[12px] font-medium uppercase text-slate-500 dark:text-slate-300',
                          h === '' && 'w-12',
                        )}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {INVOICE_ROWS.map((row) => (
                    <tr key={row.id}>
                      <td className="px-4 py-3 text-[12px] text-[#171d1c] dark:text-slate-200">{row.date}</td>
                      <td className="px-4 py-3 text-[12px] text-[#171d1c] dark:text-slate-200">{row.id}</td>
                      <td className="px-4 py-3 text-[12px] text-[#171d1c] dark:text-slate-200">{row.amount}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center border border-[0.5px] border-teal-100 bg-teal-50 px-2 py-0.5 text-[10px] font-medium uppercase text-teal-700 dark:border-teal-500/30 dark:bg-teal-950/50 dark:text-teal-300">
                          {row.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          className="inline-flex text-slate-400 hover:text-[#171d1c] dark:hover:text-slate-200"
                          aria-label={`Download ${row.id}`}
                        >
                          <Download className="h-[18px] w-[18px]" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-[0.5px] border-slate-100 bg-slate-50/30 p-3 text-center dark:border-slate-700 dark:bg-slate-800/30">
              <button
                type="button"
                className="text-[11px] font-bold uppercase tracking-widest text-slate-500 transition-colors hover:text-teal-600 dark:text-slate-300 dark:hover:text-teal-400"
              >
                View All Billing History
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
