const cols = [
  {
    title: "Your real experience, first",
    body: "Upload or paste your résumé once. Doubow uses what you provide—no invented employers, dates, or credentials.",
  },
  {
    title: "Materials that fit each posting",
    body: "For each saved role, get suggestions shaped to that job’s wording and requirements—not one copy-paste for everyone.",
  },
  {
    title: "You stay in the sender’s seat",
    body: "Apply on official career sites yourself. With Gmail, use drafts you edit and send from your own address.",
  },
];

export function ProcessStrip() {
  return (
    <section className="landing-section-y border-b border-zinc-200/80 bg-zinc-50">
      <div className="mx-auto grid max-w-6xl gap-4 px-4 sm:grid-cols-3 sm:px-6 lg:px-8">
        {cols.map((c) => (
          <div
            key={c.title}
            className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm shadow-zinc-950/5 sm:p-7"
          >
            <h3 className="text-lg font-bold text-black">{c.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-neutral-700">{c.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
