"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { useState } from "react";

const tiers = [
  {
    name: "Free",
    monthly: "€0",
    yearly: "€0",
    blurb: "Try the workspace: save jobs, get suggestion previews, and see how materials are tailored—within monthly limits.",
    featured: false,
    features: [
      "Limited jobs & AI assists per month",
      "Résumé upload or paste (your source profile)",
      "Application wording suggestions per role",
      "Dashboard: track stages and open real postings yourself",
      "Interview practice (where enabled)",
      "Email support",
      "Gmail draft saving may require a paid plan",
    ],
    includedLabel: "Included",
  },
  {
    name: "Pro",
    monthly: "€12",
    yearly: "€10",
    blurb: "More room to run your search: higher limits, Gmail drafts you edit and send, and richer prep.",
    features: [
      "Higher job + assist quotas",
      "Gmail: save application emails as drafts (you send)",
      "Richer tailored materials per posting",
      "Smart prep for batch drafting (when you turn it on)",
      "Interview practice from the same job context",
      "Priority support where offered",
    ],
    includedLabel: "Everything in Free, plus:",
    featured: true,
  },
  {
    name: "Business",
    monthly: "€39",
    yearly: "€31",
    blurb: "For coaches and teams helping several people job search at once.",
    featured: false,
    features: [
      "Seat management",
      "Shared templates & snippets",
      "Usage and success reporting",
      "Export audit logs",
      "Custom retention options",
      "Dedicated success contact",
      "SSO-ready roadmap slots",
    ],
    includedLabel: "Everything in Pro, plus:",
  },
] as const;

export function Pricing() {
  const [yearly, setYearly] = useState(false);

  return (
    <section id="pricing" className="landing-section-y landing-surface border-b border-zinc-800/80">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <h2 className="landing-heading max-w-xl text-balance">
            Choose your plan. Start today.
          </h2>
          <p className="landing-lede max-w-md lg:text-right">
            Free to explore; Pro unlocks tailored resume exports and applying
            through your own email with full approval control.
          </p>
        </div>

        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <div className="relative inline-flex rounded-full border border-zinc-700 bg-zinc-900 p-1 shadow-sm shadow-zinc-950/20">
            <span
              className={`absolute bottom-1 top-1 w-[calc(50%-4px)] rounded-full bg-emerald-500 transition-all duration-200 ${
                yearly ? "left-[calc(50%+2px)]" : "left-1"
              }`}
              aria-hidden
            />
            <button
              type="button"
              onClick={() => setYearly(false)}
              className={`relative z-10 rounded-full px-6 py-2 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 ${
                !yearly ? "text-zinc-950" : "text-zinc-400"
              }`}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setYearly(true)}
              className={`relative z-10 inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 ${
                yearly ? "text-zinc-950" : "text-zinc-400"
              }`}
            >
              Yearly
              <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-300 ring-1 ring-emerald-500/25">
                20% OFF
              </span>
            </button>
          </div>
        </div>

        <p className="mt-8 text-center text-sm text-zinc-400">
          Ready to subscribe? Open{" "}
          <a
            href="/auth/sign-up"
            className="rounded font-semibold text-zinc-100 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2"
          >
            Doubow plans &amp; billing
          </a>{" "}
          and finish checkout from your account.
        </p>

        <div className="mt-10 grid gap-2.5 lg:grid-cols-3">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`relative flex flex-col overflow-hidden rounded-2xl border p-6 sm:p-7 ${
                tier.featured
                  ? "border-emerald-500/35 bg-zinc-950 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500/25"
                  : "border-zinc-800 bg-zinc-950 shadow-sm shadow-zinc-950/30"
              }`}
            >
              {tier.featured ? (
                <span className="absolute right-4 top-4 rounded-full bg-emerald-500 px-2.5 py-0.5 text-[10px] font-bold uppercase text-zinc-950">
                  Popular
                </span>
              ) : null}
              <h3 className="text-base font-bold text-zinc-100 sm:text-lg">{tier.name}</h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-semibold tabular-nums text-zinc-100 sm:text-4xl">
                  {yearly ? tier.yearly : tier.monthly}
                </span>
                <span className="text-sm text-zinc-500">/month</span>
              </div>
              <p className="mt-3 text-sm text-zinc-400">{tier.blurb}</p>
              <a
                href={tier.name === "Free" ? "/auth/sign-up" : "/discover"}
                className={`mt-8 inline-flex h-11 justify-center rounded-full px-5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${
                  tier.featured
                    ? "border border-emerald-500 bg-emerald-500 text-zinc-950 shadow-md shadow-emerald-500/20 hover:border-emerald-400 hover:bg-emerald-400 focus-visible:ring-emerald-400 focus-visible:ring-offset-zinc-950"
                    : "border border-zinc-700 bg-zinc-900 text-zinc-100 shadow-sm hover:border-zinc-600 hover:bg-zinc-800 focus-visible:ring-zinc-500 focus-visible:ring-offset-zinc-950"
                }`}
              >
                {tier.name === "Free" ? "Create account" : "Subscribe"}
              </a>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center" aria-hidden>
                  <div className="w-full border-t border-zinc-800" />
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-zinc-950 px-3 text-xs font-medium text-zinc-500">
                    {tier.includedLabel}
                  </span>
                </div>
              </div>

              <ul className="space-y-3 text-sm text-zinc-400">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" strokeWidth={1.75} />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
