import Link from "next/link";
import { Star, ShieldCheck, Sparkles } from "lucide-react";
import { DashboardPreview } from "@/components/doubow/DashboardPreview";

export function Hero() {
  return (
    <section
      id="product"
      className="relative overflow-hidden border-b border-zinc-200/80 bg-zinc-50"
    >
      {/* subtle depth — keeps hero readable without heavy illustration */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_60%_at_50%_-15%,rgba(79,70,229,0.09),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-y-0 right-0 w-1/2 max-w-xl bg-[radial-gradient(circle_at_70%_30%,rgba(79,70,229,0.06),transparent_65%)]"
        aria-hidden
      />

      <div className="relative mx-auto max-w-6xl px-4 pb-14 pt-14 sm:px-6 sm:pb-16 sm:pt-20 lg:px-8 lg:pb-20 lg:pt-24">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-center lg:gap-14">
          <div className="text-center lg:text-left">
            <div
              className="inline-flex opacity-0 motion-reduce:animate-none motion-reduce:opacity-100 animate-landing-rise items-center gap-2 rounded-full border border-zinc-200/90 bg-white/90 px-3 py-1.5 text-2xs font-semibold uppercase tracking-[0.18em] text-indigo-600 shadow-sm ring-1 ring-indigo-500/10 backdrop-blur-sm"
            >
              <Sparkles size={12} aria-hidden />
              Human-in-the-loop career agent
            </div>

            <h1 className="font-display mt-6 max-w-[22ch] text-balance text-4xl font-semibold leading-[1.06] tracking-tight text-zinc-950 opacity-0 motion-reduce:animate-none motion-reduce:opacity-100 animate-landing-rise-delayed sm:text-5xl lg:max-w-none lg:text-[3.25rem] lg:leading-[1.05]">
              A calmer way to run your job search
            </h1>

            <p className="landing-lede mx-auto mt-6 max-w-xl text-pretty opacity-0 motion-reduce:animate-none motion-reduce:opacity-100 animate-landing-rise-delayed-2 lg:mx-0">
              Doubow helps you discover better-fit roles, tailor materials with your real resume data, and stay ready
              for interviews. The automation is fast, but approvals stay in your hands.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-3 lg:justify-start">
              <Link href="/discover" className="landing-btn-primary px-8 py-3.5">
                Get started now
              </Link>
              <a href="#pricing" className="landing-btn-secondary px-7 py-3.5">
                See pricing
              </a>
            </div>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-3 text-sm text-zinc-600 lg:justify-start">
              <span className="text-zinc-500">Doubow members</span>
              <span className="flex gap-0.5" role="img" aria-label="5 out of 5 stars">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className="h-4 w-4 fill-indigo-600 text-indigo-600"
                    strokeWidth={0}
                  />
                ))}
              </span>
              <span className="font-semibold tabular-nums text-zinc-950">4.9</span>
              <span
                className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white"
                aria-hidden
              >
                D
              </span>
            </div>
          </div>

          <div className="mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 lg:gap-4">
              <div className="rounded-2xl border border-zinc-200/90 bg-white px-4 py-4 text-left shadow-sm shadow-zinc-950/[0.04] ring-1 ring-zinc-950/[0.02] transition hover:border-zinc-300 hover:shadow-md hover:shadow-zinc-950/[0.06]">
                <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">
                  Time to first matches
                </p>
                <p className="mt-1 text-lg font-semibold tabular-nums text-zinc-950">~2 min</p>
              </div>
              <div className="rounded-2xl border border-zinc-200/90 bg-white px-4 py-4 text-left shadow-sm shadow-zinc-950/[0.04] ring-1 ring-zinc-950/[0.02] transition hover:border-zinc-300 hover:shadow-md hover:shadow-zinc-950/[0.06]">
                <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Approval safety</p>
                <p className="mt-1 flex items-center gap-1.5 text-lg font-semibold text-zinc-950">
                  <ShieldCheck size={16} className="shrink-0 text-indigo-600" strokeWidth={2} />
                  Always-on gate
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-200/90 bg-white px-4 py-4 text-left shadow-sm shadow-zinc-950/[0.04] ring-1 ring-zinc-950/[0.02] transition hover:border-zinc-300 hover:shadow-md hover:shadow-zinc-950/[0.06]">
                <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Fit scoring</p>
                <p className="mt-1 text-lg font-semibold tabular-nums text-zinc-950">5 dimensions</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <DashboardPreview />
    </section>
  );
}
