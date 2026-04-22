import Link from "next/link";
import { Star, ShieldCheck, Sparkles } from "lucide-react";
import { DashboardPreview } from "@/components/doubow/DashboardPreview";

export function Hero() {
  return (
    <section
      id="product"
      className="landing-surface relative overflow-hidden border-b border-zinc-800/80"
    >
      {/* subtle depth — keeps hero readable without heavy illustration */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_60%_at_50%_-15%,rgba(16,185,129,0.12),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-y-0 right-0 w-1/2 max-w-xl bg-[radial-gradient(circle_at_70%_30%,rgba(52,211,153,0.08),transparent_65%)]"
        aria-hidden
      />

      <div className="relative mx-auto max-w-6xl px-4 pb-14 pt-14 sm:px-6 sm:pb-16 sm:pt-20 lg:px-8 lg:pb-20 lg:pt-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="inline-flex opacity-0 motion-reduce:animate-none motion-reduce:opacity-100 animate-landing-rise items-center gap-2 rounded-full border border-zinc-700 bg-zinc-900/80 px-3 py-1.5 text-2xs font-semibold uppercase tracking-[0.18em] text-emerald-300 shadow-sm ring-1 ring-emerald-500/20 backdrop-blur-sm">
            <Sparkles size={12} aria-hidden />
            Human-in-the-loop career agent
          </div>

          <h1 className="font-display mx-auto mt-6 max-w-[18ch] text-balance text-4xl font-medium leading-[1.07] tracking-tight text-zinc-100 opacity-0 motion-reduce:animate-none motion-reduce:opacity-100 animate-landing-rise-delayed sm:text-5xl lg:text-[3.35rem] lg:leading-[1.04]">
            A calmer way to run your job search
          </h1>

          <p className="landing-lede mx-auto mt-6 max-w-2xl text-pretty opacity-0 motion-reduce:animate-none motion-reduce:opacity-100 animate-landing-rise-delayed-2">
            Doubow helps you discover better-fit roles, tailor materials with your real resume data, and stay ready
            for interviews. The automation is fast, but approvals stay in your hands.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/discover" className="landing-btn-primary px-8 py-3.5">
              Get started now
            </Link>
            <a href="#pricing" className="landing-btn-secondary px-7 py-3.5">
              See pricing
            </a>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-3 text-sm text-zinc-400">
            <span className="text-zinc-500">Doubow members</span>
            <span className="flex gap-0.5" role="img" aria-label="5 out of 5 stars">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className="h-4 w-4 fill-emerald-400 text-emerald-400"
                  strokeWidth={0}
                />
              ))}
            </span>
            <span className="font-medium tabular-nums text-zinc-100">4.9</span>
            <span
              className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500 text-xs font-bold text-zinc-950"
              aria-hidden
            >
              D
            </span>
          </div>

          <div className="mx-auto mt-10 grid max-w-3xl gap-3 sm:grid-cols-3">
            <div className="landing-panel rounded-2xl px-4 py-4 text-left transition hover:-translate-y-0.5">
              <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">
                Time to first matches
              </p>
              <p className="mt-1 text-lg font-medium tabular-nums text-zinc-100">~2 min</p>
            </div>
            <div className="landing-panel rounded-2xl px-4 py-4 text-left transition hover:-translate-y-0.5">
              <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Approval safety</p>
              <p className="mt-1 flex items-center gap-1.5 text-lg font-medium text-zinc-100">
                <ShieldCheck size={16} className="shrink-0 text-emerald-400" strokeWidth={2} />
                Always-on gate
              </p>
            </div>
            <div className="landing-panel rounded-2xl px-4 py-4 text-left transition hover:-translate-y-0.5">
              <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Fit scoring</p>
              <p className="mt-1 text-lg font-medium tabular-nums text-zinc-100">5 dimensions</p>
            </div>
          </div>
        </div>
      </div>

      <DashboardPreview />
    </section>
  );
}
