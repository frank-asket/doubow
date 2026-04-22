import Link from "next/link";
import { ChevronDown } from "lucide-react";

const steps = [
  {
    n: "1",
    title: "Add your résumé (and Gmail if you like)",
    body: "Sign in, upload or paste your experience, and optionally connect Gmail so application emails can be saved as drafts you review and send yourself.",
    mock: "signup",
  },
  {
    n: "2",
    title: "Shape materials for each role",
    body: "Save jobs you find, then get wording tuned to what each posting asks for—grounded in your real résumé, not a generic blast.",
    mock: "fund",
  },
  {
    n: "3",
    title: "Apply on the real site",
    body: "You open the employer or LinkedIn posting and submit there yourself. For email applications, start from a Gmail draft if you created one—Doubow never auto-submits.",
    mock: "trade",
  },
] as const;

function MockSignup() {
  return (
    <div className="mt-6 space-y-2 rounded-xl border border-neutral-300 bg-neutral-50 p-3">
      <div className="h-8 rounded-lg bg-white px-2 text-[10px] leading-8 text-neutral-700">
        Resume PDF uploaded
      </div>
      <div className="flex h-8 items-center justify-between rounded-lg bg-white px-2 text-[10px] text-neutral-700">
        <span>Inbox connected</span>
        <span className="text-neutral-1000">Active</span>
      </div>
    </div>
  );
}

function MockFund() {
  return (
    <div className="mt-6 space-y-2 rounded-xl border border-neutral-300 bg-neutral-50 p-3">
      <p className="text-[10px] text-neutral-700">Output for Metro Health · ICU Nurse</p>
      <div className="flex h-9 items-center justify-between rounded-lg border border-neutral-300 bg-white px-2">
        <span className="truncate text-xs text-neutral-1000">Resume_Alex_MetroHealth_ICUNurse.pdf</span>
        <span className="flex items-center gap-1 text-[10px] font-medium text-neutral-900">
          Tailored
          <ChevronDown className="h-3 w-3 opacity-60" />
        </span>
      </div>
    </div>
  );
}

function MockTrade() {
  return (
    <div className="mt-6 space-y-2 rounded-xl border border-neutral-300 bg-neutral-50 p-3">
      <div className="flex items-center justify-between rounded-lg bg-white px-2 py-2 text-[10px] text-neutral-700">
        <span>From</span>
        <span className="font-mono text-neutral-900">you@domain.com</span>
      </div>
      <div className="flex items-center justify-between rounded-lg bg-white px-2 py-2 text-[11px]">
        <span className="text-neutral-600">Status</span>
        <span className="text-neutral-1000">Draft ready</span>
      </div>
    </div>
  );
}

export function HowItWorks() {
  return (
    <section id="how" className="landing-section-y border-b border-zinc-200/80 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="landing-heading text-balance">
              How it works
            </h2>
            <p className="landing-lede mt-4 max-w-xl">
              From your résumé to <span className="text-neutral-900">saved roles</span> to{" "}
              <span className="text-neutral-900">clear application materials per job</span>—with you
              choosing when and where to hit submit.
            </p>
          </div>
          <Link
            href="/discover"
            className="inline-flex items-center gap-1 rounded-md text-sm font-semibold text-neutral-800 transition hover:text-neutral-1000 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
          >
            Create account now <span aria-hidden>&gt;</span>
          </Link>
        </div>

        <div className="mt-10 grid gap-2.5 md:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.n}
              className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm shadow-zinc-950/5 transition-colors duration-150 hover:border-zinc-300 hover:shadow-md hover:shadow-zinc-950/10 sm:p-7"
            >
              <span className="text-2xl font-bold text-indigo-600">{step.n}</span>
              <h3 className="mt-2.5 text-base font-bold text-black sm:text-lg">{step.title}</h3>
              <p className="mt-2 text-sm text-neutral-700">{step.body}</p>
              {step.mock === "signup" ? <MockSignup /> : null}
              {step.mock === "fund" ? <MockFund /> : null}
              {step.mock === "trade" ? <MockTrade /> : null}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
