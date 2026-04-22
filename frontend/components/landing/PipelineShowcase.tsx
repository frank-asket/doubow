import Link from "next/link";

const roles = [
  { title: "ICU Nurse", company: "Metro Health", match: "94%", delta: "+4.2%", up: true },
  { title: "Warehouse Lead", company: "Continental Line", match: "89%", delta: "+2.1%", up: true },
  { title: "High School Teacher", company: "Northfield District", match: "87%", delta: "-0.6%", up: false },
  { title: "Field Accountant", company: "Summit Co-op", match: "91%", delta: "+3.4%", up: true },
  { title: "DevOps Engineer", company: "Ioncraft", match: "85%", delta: "+1.8%", up: true },
];

function Initial({ name }: { name: string }) {
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/15 text-xs font-bold text-emerald-300">
      {name.slice(0, 1)}
    </span>
  );
}

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
            className="landing-link-accent mt-6 inline-flex items-center gap-1 rounded-md text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
          >
            Open dashboard <span aria-hidden>&gt;</span>
          </Link>
        </div>
        <div className="mt-1 flex flex-wrap justify-center gap-3 sm:justify-end">
          {roles.concat(roles).map((c, i) => (
            <div
              key={`${c.title}-${i}`}
              className="landing-panel flex min-w-[140px] flex-col gap-2 rounded-2xl p-4 transition hover:-translate-y-0.5"
            >
              <div className="flex items-center gap-2">
                <Initial name={c.company} />
                <span className="text-sm font-semibold text-zinc-100">{c.title}</span>
              </div>
              <p className="text-xs text-zinc-500">{c.company}</p>
              <p className="font-mono text-sm text-zinc-100">{c.match}</p>
              <p
                className={`text-xs font-semibold ${
                  c.up ? "text-emerald-300" : "text-zinc-500"
                }`}
              >
                {c.delta}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
