import Link from "next/link";

/** Narrative block: résumé loop + Doubow’s guardrailed assistant (not a public “digital twin” product). */
export function FutureOfResumes() {
  return (
    <section
      id="future-resumes"
      className="landing-section-y landing-surface border-b border-zinc-800/80"
    >
      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
          The future of résumés
        </p>
        <h2 className="landing-heading mt-5 max-w-3xl text-balance">
          Stop rewriting the same story for every posting
        </h2>
        <div className="landing-panel mt-8 rounded-2xl p-6 text-left sm:p-8">
          <div className="space-y-4 text-base leading-relaxed text-zinc-400 sm:text-lg">
            <p>
              The old loop: hours tweaking bullets and summaries so you sound right for{" "}
              <em className="landing-copy-strong not-italic">this</em> recruiter and{" "}
              <em className="landing-copy-strong not-italic">that</em> ATS—then doing it again tomorrow.
            </p>
            <p>
              <span className="landing-copy-strong">Doubow starts from your real résumé and credentials</span>{" "}
              (nothing invented), then helps you shape{" "}
              <span className="landing-copy-strong">application-specific wording, checklists, and interview prep</span>{" "}
              per role. It&apos;s a <span className="landing-copy-strong">guardrailed assistant inside your workspace</span>
              —not a public chatbot pretending to be you, and not auto-submitting on employer sites.
            </p>
            <p className="text-sm text-zinc-500 sm:text-base">
              You review and edit; you click Apply and Send. That&apos;s the balance between leverage and trust.
            </p>
          </div>
        </div>
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <a
            href="/auth/sign-up"
            className="landing-btn-primary px-8 py-3.5"
          >
            Open your workspace
          </a>
          <Link
            href="/discover"
            className="text-sm font-semibold text-zinc-300 underline-offset-4 hover:text-zinc-100 hover:underline"
          >
            Already signed in →
          </Link>
        </div>
      </div>
    </section>
  );
}
