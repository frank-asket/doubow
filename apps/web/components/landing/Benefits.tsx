import { FileUser, Mail, BadgeCheck, LayoutGrid } from "lucide-react";

const items = [
  {
    title: "Per-job wording from your résumé",
    body: "Get ideas for bullets, letters, and notes aligned to each listing—not one generic CV blast for every employer.",
    icon: FileUser,
  },
  {
    title: 'Optional Gmail drafts',
    body: "Connect Google if you want application emails saved as drafts. You review and send; employers see your address.",
    icon: Mail,
  },
  {
    title: 'Honest to each posting',
    body: "Suggestions reflect that employer’s requirements and tone. You adjust everything before you use it.",
    icon: BadgeCheck,
  },
  {
    title: 'One calm workspace',
    body: "Saved jobs, application prep, and interview practice share the same context—less context-switching.",
    icon: LayoutGrid,
  },
]

export function Benefits() {
  return (
    <section id="why" className="landing-section-y landing-surface border-b border-zinc-800/80">
      <div className="mx-auto max-w-6xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="landing-heading text-balance">
          Why choose Doubow?
        </h2>
        <p className="landing-lede mx-auto mt-4 max-w-2xl text-pretty">
          Built for <span className="landing-copy-strong font-medium">people in any field</span>: care, trades,
          office work, clinical roles, hospitality, technology—any title you’re pursuing. You
          keep control of applying; we help with preparation and clarity.
        </p>

        <div className="mt-9 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <article
                key={item.title}
                className="landing-panel rounded-2xl p-6 text-left transition duration-150 hover:-translate-y-0.5"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-zinc-700 bg-zinc-900 text-zinc-300">
                  <Icon className="h-5 w-5" strokeWidth={1.75} />
                </div>
                <h3 className="mt-4 text-base font-bold text-zinc-100 sm:text-lg">
                  {item.title}
                </h3>
                <p className="landing-copy-muted mt-2 text-sm leading-relaxed">
                  {item.body}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
