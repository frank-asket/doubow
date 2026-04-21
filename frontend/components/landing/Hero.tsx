import Link from "next/link";
import { Star, ShieldCheck, Sparkles } from "lucide-react";
import { DashboardPreview } from "@/components/doubow/DashboardPreview";

export function Hero() {
  return (
    <section id="product" className="border-b border-neutral-300/70">
      <div className="mx-auto max-w-6xl px-4 pb-8 pt-14 sm:px-6 sm:pt-20 lg:px-8 lg:pt-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary-500/40 bg-primary-500/10 px-3 py-1 text-2xs font-medium uppercase tracking-[0.18em] text-neutral-900">
            <Sparkles size={12} />
            Human-in-the-loop career agent
          </div>
          <h1 className="mt-4 text-4xl font-semibold leading-tight tracking-tight text-neutral-1000 sm:text-5xl lg:text-[3.3rem] lg:leading-[1.06]">
            A calmer way to run your job search
          </h1>
          <p className="mx-auto mt-4 max-w-3xl text-base leading-relaxed text-neutral-700 sm:text-lg">
            Doubow helps you discover better-fit roles, tailor materials with your real resume data, and stay ready
            for interviews. The automation is fast, but approvals stay in your hands.
          </p>
        </div>

        <div className="mx-auto mt-6 grid max-w-4xl gap-2.5 sm:grid-cols-3">
          <div className="rounded-xl border border-neutral-300 bg-white px-3.5 py-3 text-left">
            <p className="text-2xs uppercase tracking-wider text-neutral-600">Time to first matches</p>
            <p className="mt-1 text-lg font-semibold text-neutral-1000">~2 min</p>
          </div>
          <div className="rounded-xl border border-neutral-300 bg-white px-3.5 py-3 text-left">
            <p className="text-2xs uppercase tracking-wider text-neutral-600">Approval safety</p>
            <p className="mt-1 flex items-center gap-1 text-lg font-semibold text-neutral-1000">
              <ShieldCheck size={14} className="text-neutral-1000" />
              Always-on gate
            </p>
          </div>
          <div className="rounded-xl border border-neutral-300 bg-white px-3.5 py-3 text-left">
            <p className="text-2xs uppercase tracking-wider text-neutral-600">Fit scoring</p>
            <p className="mt-1 text-lg font-semibold text-neutral-1000">5 dimensions</p>
          </div>
        </div>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/discover"
            className="inline-flex rounded-full bg-primary-500 px-8 py-3.5 text-sm font-semibold text-black shadow-[0_16px_40px_-18px_rgba(255,188,1,0.8)] transition hover:bg-primary-600"
          >
            Get started now
          </Link>
          <a
            href="/auth/sign-up"
            className="inline-flex rounded-full border border-neutral-400 px-7 py-3.5 text-sm font-semibold text-neutral-800 transition hover:border-neutral-700 hover:text-neutral-1000"
          >
            See pricing
          </a>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3 text-sm text-neutral-700">
          <span className="text-neutral-500">Doubow members</span>
          <span className="flex gap-0.5" role="img" aria-label="5 out of 5 stars">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className="h-4 w-4 fill-primary-500 text-primary-500"
                strokeWidth={0}
              />
            ))}
          </span>
          <span className="font-semibold text-neutral-1000">4.9</span>
          <span
            className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-500 text-xs font-bold text-black"
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
