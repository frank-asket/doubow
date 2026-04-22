import Link from "next/link";
import { Star, ShieldCheck, Sparkles } from "lucide-react";
import { DashboardPreview } from "@/components/doubow/DashboardPreview";

export function Hero() {
  return (
    <section
      id="product"
      className="border-b border-zinc-200/80 bg-gradient-to-b from-white via-zinc-50/90 to-zinc-50"
    >
      <div className="mx-auto max-w-6xl px-4 pb-8 pt-14 sm:px-6 sm:pt-20 lg:px-8 lg:pt-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1 text-2xs font-semibold uppercase tracking-[0.2em] text-indigo-600 shadow-sm ring-1 ring-indigo-500/10">
            <Sparkles size={12} />
            Human-in-the-loop career agent
          </div>
          <h1 className="mt-5 text-4xl font-bold capitalize leading-[1.08] tracking-tight text-black sm:text-5xl lg:text-[3.25rem]">
            A calmer way to run your job search
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-zinc-600 sm:text-lg">
            Doubow helps you discover better-fit roles, tailor materials with your real resume data, and stay ready
            for interviews. The automation is fast, but approvals stay in your hands.
          </p>
        </div>

        <div className="mx-auto mt-8 grid max-w-4xl gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-4 text-left shadow-sm shadow-zinc-950/5">
            <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">
              Time to first matches
            </p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-zinc-950">~2 min</p>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-4 text-left shadow-sm shadow-zinc-950/5">
            <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Approval safety</p>
            <p className="mt-1 flex items-center gap-1.5 text-lg font-semibold text-zinc-950">
              <ShieldCheck size={16} className="shrink-0 text-indigo-600" strokeWidth={2} />
              Always-on gate
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-4 text-left shadow-sm shadow-zinc-950/5">
            <p className="text-2xs font-medium uppercase tracking-wider text-zinc-500">Fit scoring</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-zinc-950">5 dimensions</p>
          </div>
        </div>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/discover"
            className="inline-flex rounded-full border border-indigo-600 bg-indigo-600 px-8 py-3.5 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition hover:border-indigo-700 hover:bg-indigo-700"
          >
            Get started now
          </Link>
          <a
            href="#pricing"
            className="inline-flex rounded-full border border-zinc-200 bg-white px-7 py-3.5 text-sm font-semibold text-zinc-800 shadow-sm transition hover:border-zinc-300 hover:bg-zinc-50"
          >
            See pricing
          </a>
        </div>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-3 text-sm text-zinc-600">
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

      <DashboardPreview />
    </section>
  );
}
