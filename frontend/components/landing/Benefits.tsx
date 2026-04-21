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
    <section id="why" className="border-b border-zinc-200/80 bg-zinc-50 py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-semibold tracking-tight text-zinc-950 sm:text-4xl">
          Why choose Doubow?
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-base leading-relaxed text-zinc-600 sm:text-lg">
          Built for <span className="font-medium text-zinc-900">people in any field</span>: care, trades,
          office work, clinical roles, hospitality, technology—any title you’re pursuing. You
          keep control of applying; we help with preparation and clarity.
        </p>

        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <article
                key={item.title}
                className="rounded-xl border border-zinc-200 bg-white p-5 text-left shadow-sm shadow-zinc-950/5 transition-colors duration-150 hover:border-zinc-300 sm:p-6"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 bg-zinc-50 text-indigo-600">
                  <Icon className="h-5 w-5" strokeWidth={1.75} />
                </div>
                <h3 className="mt-4 text-base font-semibold text-zinc-950 sm:text-lg">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-600">
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
