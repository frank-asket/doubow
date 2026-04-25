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
    <div className="mt-6 space-y-2 rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <div className="h-8 rounded-lg bg-zinc-900 px-2 text-[10px] leading-8 text-zinc-300">
        Resume PDF uploaded
      </div>
      <div className="flex h-8 items-center justify-between rounded-lg bg-zinc-900 px-2 text-[10px] text-zinc-300">
        <span>Inbox connected</span>
        <span className="text-zinc-100">Active</span>
      </div>
    </div>
  );
}

function MockFund() {
  return (
    <div className="mt-6 space-y-2 rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <p className="text-[10px] text-zinc-400">Output for Metro Health · ICU Nurse</p>
      <div className="flex h-9 items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-2">
        <span className="truncate text-xs text-zinc-100">resume.pdf</span>
        <span className="flex items-center gap-1 text-[10px] font-medium text-zinc-300">
          Tailored
          <ChevronDown className="h-3 w-3 opacity-60" />
        </span>
      </div>
    </div>
  );
}

function MockTrade() {
  return (
    <div className="mt-6 space-y-2 rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <div className="flex items-center justify-between rounded-lg bg-zinc-900 px-2 py-2 text-[10px] text-zinc-300">
        <span>From</span>
        <span className="font-mono text-zinc-100">you@domain.com</span>
      </div>
      <div className="flex items-center justify-between rounded-lg bg-zinc-900 px-2 py-2 text-[11px]">
        <span className="text-zinc-500">Status</span>
        <span className="text-zinc-100">Draft ready</span>
      </div>
    </div>
  );
}

export function HowItWorks() {
  return (
    <section id="how" className="landing-section-y landing-surface border-b border-zinc-800/80">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="landing-heading text-balance">
              How it works
            </h2>
            <p className="landing-lede mt-4 max-w-xl">
              From your résumé to <span className="landing-copy-strong">saved roles</span> to{" "}
              <span className="landing-copy-strong">clear application materials per job</span>—with you
              choosing when and where to hit submit.
            </p>
          </div>
          <Link
            href="/discover"
            className="landing-link-accent inline-flex items-center gap-1 rounded-md text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
          >
            Create account now <span aria-hidden>&gt;</span>
          </Link>
        </div>

        <div className="mt-9 grid gap-2.5 md:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.n}
              className="landing-panel rounded-2xl p-6 transition duration-150 hover:-translate-y-0.5 sm:p-7"
            >
              <span className="text-2xl font-bold text-zinc-300">{step.n}</span>
              <h3 className="mt-2.5 text-base font-bold text-zinc-100 sm:text-lg">{step.title}</h3>
              <p className="landing-copy-muted mt-2 text-sm">{step.body}</p>
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
