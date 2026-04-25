"use client";

import { ChevronLeft, ChevronRight, Zap } from "lucide-react";
import { useState } from "react";

const quotes = [
  {
    text: "Each posting gets tailored wording and a Gmail draft I can edit—I send when I’m ready, from my own inbox.",
    name: "Verified job seeker",
    role: "Healthcare · North America",
    initials: "V",
  },
  {
    text: "Interview prep pulled from the same packet I applied with—no more contradictory stories between the cover letter and prep.",
    name: "Verified job seeker",
    role: "Operations · Europe",
    initials: "V",
  },
  {
    text: "We use Doubow with our cohorts across industries. The clear stages make what’s next obvious.",
    name: "Career services lead",
    role: "Coaching organization",
    initials: "C",
  },
];

export function Testimonials() {
  const [i, setI] = useState(0);
  const q = quotes[i];

  return (
    <section
      id="testimonials"
      className="landing-section-y landing-surface border-b border-zinc-800/80"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <h2 className="landing-heading max-w-xl text-balance">
            Trusted by serious job seekers
          </h2>
          <p className="landing-lede max-w-md lg:text-right">
            Built for people who want leverage, transparency, and control at the
            moments that touch employers.
          </p>
        </div>

        <div className="landing-panel mt-10 flex flex-col overflow-hidden rounded-2xl lg:flex-row">
          <div className="flex flex-1 flex-col gap-6 border-b border-zinc-800 p-8 lg:border-b-0 lg:border-r lg:border-zinc-800 lg:p-10">
            <div className="flex items-center gap-3">
              <div
                className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-zinc-100 to-zinc-300 text-lg font-bold text-zinc-950 ring-2 ring-zinc-500/30"
                aria-hidden
              >
                {q.initials}
              </div>
              <span className="flex h-10 w-10 items-center justify-center rounded-full border border-zinc-700 bg-zinc-900 text-zinc-300">
                <Zap className="h-5 w-5 fill-zinc-300" strokeWidth={0} />
              </span>
            </div>
            <blockquote className="text-xl font-medium leading-snug text-zinc-100 sm:text-2xl">
              &ldquo;{q.text}&rdquo;
            </blockquote>
            <div className="mt-auto flex flex-wrap items-end justify-between gap-4 pt-4">
              <div>
                <p className="font-semibold text-zinc-100">{q.name}</p>
                <p className="text-sm text-zinc-500">{q.role}</p>
              </div>
              <p className="text-sm font-medium tabular-nums text-zinc-500">
                {i + 1}/{quotes.length}
              </p>
            </div>
          </div>
          <div className="flex flex-row justify-stretch divide-x divide-zinc-800 bg-zinc-950/80 lg:w-52 lg:flex-col lg:divide-x-0 lg:divide-y lg:divide-zinc-800">
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 py-6 text-sm font-medium text-zinc-300 transition hover:bg-zinc-900 hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-zinc-300 lg:flex-none"
              onClick={() => setI((v) => (v - 1 + quotes.length) % quotes.length)}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 py-6 text-sm font-medium text-zinc-300 transition hover:bg-zinc-900 hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-zinc-300 lg:flex-none"
              onClick={() => setI((v) => (v + 1) % quotes.length)}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
