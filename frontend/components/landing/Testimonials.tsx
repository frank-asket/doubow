"use client";

import { ChevronLeft, ChevronRight, Zap } from "lucide-react";
import { useState } from "react";

const quotes = [
  {
    text: "Each posting gets tailored wording and a Gmail draft I can edit—I send when I’m ready, from my own inbox.",
    name: "Alex M.",
    role: "Registered nurse · Toronto",
    initials: "A",
  },
  {
    text: "Interview prep pulled from the same packet I applied with—no more contradictory stories between the cover letter and prep.",
    name: "Jordan K.",
    role: "Operations supervisor · Rotterdam",
    initials: "J",
  },
  {
    text: "We use Doubow with our cohorts—health, logistics, office, tech. The clear stages make what’s next obvious.",
    name: "Samira L.",
    role: "Career coach",
    initials: "S",
  },
];

export function Testimonials() {
  const [i, setI] = useState(0);
  const q = quotes[i];

  return (
    <section id="testimonials" className="border-b border-neutral-300/70 bg-white py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <h2 className="max-w-xl text-3xl font-semibold tracking-tight text-neutral-1000 sm:text-4xl">
            Trusted by serious job seekers
          </h2>
          <p className="max-w-md text-lg text-neutral-700 lg:text-right">
            Built for people who want leverage, transparency, and control at the
            moments that touch employers.
          </p>
        </div>

        <div className="mt-14 flex flex-col overflow-hidden rounded-2xl border border-neutral-300 bg-white lg:flex-row">
          <div className="flex flex-1 flex-col gap-6 border-b border-neutral-300 p-8 lg:border-b-0 lg:border-r lg:border-neutral-300 lg:p-10">
            <div className="flex items-center gap-3">
              <div
                className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-lg font-bold text-black ring-2 ring-primary-500/40"
                aria-hidden
              >
                {q.initials}
              </div>
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-500/20 text-neutral-1000">
                <Zap className="h-5 w-5 fill-primary-500" strokeWidth={0} />
              </span>
            </div>
            <blockquote className="text-xl font-medium leading-snug text-neutral-1000 sm:text-2xl">
              &ldquo;{q.text}&rdquo;
            </blockquote>
            <div className="mt-auto flex flex-wrap items-end justify-between gap-4 pt-4">
              <div>
                <p className="font-semibold text-neutral-1000">{q.name}</p>
                <p className="text-sm text-neutral-500">{q.role}</p>
              </div>
              <p className="text-sm text-neutral-500">
                {i + 1}/{quotes.length}
              </p>
            </div>
          </div>
          <div className="flex flex-row justify-stretch divide-x divide-neutral-300 lg:w-52 lg:flex-col lg:divide-x-0 lg:divide-y">
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 py-6 text-sm font-medium text-neutral-500 transition hover:bg-neutral-50 hover:text-neutral-1000 lg:flex-none"
              onClick={() => setI((v) => (v - 1 + quotes.length) % quotes.length)}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 py-6 text-sm font-medium text-neutral-500 transition hover:bg-neutral-50 hover:text-neutral-1000 lg:flex-none"
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
