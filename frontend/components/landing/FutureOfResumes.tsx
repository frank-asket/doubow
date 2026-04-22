import Link from "next/link";

/** Narrative block: résumé loop + Doubow’s guardrailed assistant (not a public “digital twin” product). */
export function FutureOfResumes() {
  return (
    <section
      id="future-resumes"
      className="border-b border-zinc-200/80 bg-white py-20 sm:py-24"
    >
      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
          The future of résumés
        </p>
        <h2 className="mt-4 text-3xl font-bold capitalize tracking-tight text-black sm:text-4xl">
          Stop rewriting the same story for every posting
        </h2>
        <div className="mt-8 rounded-2xl border border-zinc-200 bg-zinc-50/80 p-6 text-left shadow-sm shadow-zinc-950/5 sm:p-8">
          <div className="space-y-4 text-base leading-relaxed text-neutral-700 sm:text-lg">
            <p>
              The old loop: hours tweaking bullets and summaries so you sound right for{" "}
              <em className="text-neutral-900 not-italic">this</em> recruiter and{" "}
              <em className="text-neutral-900 not-italic">that</em> ATS—then doing it again tomorrow.
            </p>
            <p>
              <span className="text-neutral-1000">Doubow starts from your real résumé and credentials</span>{" "}
              (nothing invented), then helps you shape{" "}
              <span className="text-neutral-1000">application-specific wording, checklists, and interview prep</span>{" "}
              per role. It&apos;s a <span className="text-neutral-1000">guardrailed assistant inside your workspace</span>
              —not a public chatbot pretending to be you, and not auto-submitting on employer sites.
            </p>
            <p className="text-sm text-neutral-500 sm:text-base">
              You review and edit; you click Apply and Send. That&apos;s the balance between leverage and trust.
            </p>
          </div>
        </div>
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <a
            href="/auth/sign-up"
            className="inline-flex rounded-full bg-indigo-600 px-8 py-3.5 text-sm font-semibold text-white shadow-[0_16px_40px_-18px_rgba(67,56,202,0.55)] transition hover:bg-indigo-700"
          >
            Open your workspace
          </a>
          <Link
            href="/discover"
            className="text-sm font-semibold text-neutral-700 underline-offset-4 hover:text-neutral-1000 hover:underline"
          >
            Already signed in →
          </Link>
        </div>
      </div>
    </section>
  );
}
