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
    <section id="how" className="border-b border-[#e7e8ee] bg-[#f3f4f8] py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-neutral-1000 sm:text-4xl">
              How it works
            </h2>
            <p className="mt-3 max-w-xl text-base leading-relaxed text-neutral-700 sm:text-lg">
              From your résumé to <span className="text-neutral-900">saved roles</span> to{" "}
              <span className="text-neutral-900">clear application materials per job</span>—with you
              choosing when and where to hit submit.
            </p>
          </div>
          <Link
            href="/discover"
            className="inline-flex items-center gap-1 text-sm font-semibold text-neutral-800 hover:text-neutral-1000"
          >
            Create account now <span aria-hidden>&gt;</span>
          </Link>
        </div>

        <div className="mt-10 grid gap-2.5 md:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.n}
              className="rounded-xl border border-neutral-300 bg-white p-5 transition-colors duration-150 hover:border-neutral-400 sm:p-6"
            >
              <span className="text-2xl font-semibold text-indigo-600">{step.n}</span>
              <h3 className="mt-2.5 text-base font-semibold text-neutral-1000 sm:text-lg">{step.title}</h3>
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
