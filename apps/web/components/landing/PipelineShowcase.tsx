import Link from "next/link";
import Image from "next/image";
import dashboardScreenshot from "@/tests/dashboard_visual.spec.ts-snapshots/dashboard-tablet-1024-firefox-darwin.png";

export function PipelineShowcase() {
  return (
    <section id="pipeline-showcase" className="landing-section-y landing-surface border-b border-zinc-800/80">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:items-center lg:px-8">
        <div>
          <h2 className="landing-heading text-balance">
            Every sector, matched worldwide
          </h2>
          <p className="landing-lede mt-5 max-w-xl">
            Nurses, teachers, drivers, clinicians, accountants, technicians—Doubow is for anyone
            updating their career. Save roles you find (or ideas from our search helper), then get{" "}
            <span className="landing-copy-strong">tailored wording</span> and a clear path to{" "}
            <span className="landing-copy-strong">apply on the real site</span>. Connect Gmail if you want
            application emails saved as <span className="landing-copy-strong">drafts</span> to edit and send.
          </p>
          <Link
            href="/discover"
            className="landing-link-accent mt-6 inline-flex items-center gap-1 rounded-md text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
          >
            Open dashboard <span aria-hidden>&gt;</span>
          </Link>
        </div>
        <div className="mt-1 sm:justify-end">
          <div className="landing-panel overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/40 p-2 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
            <div className="mb-2 flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/70 px-3 py-1.5">
              <span className="text-[11px] font-medium tracking-wide text-zinc-300">Real product screenshot</span>
              <span className="text-[11px] text-zinc-500">Dashboard</span>
            </div>
            <Image
              src={dashboardScreenshot}
              alt="Doubow dashboard preview"
              priority
              className="h-auto w-full rounded-xl border border-zinc-800 object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
