import { Bell, Search } from "lucide-react";

function BottomRow() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {["My jobs", "Help", "Support"].map((t) => (
        <div
          key={t}
          className="rounded-2xl border border-zinc-800 bg-[#0c0c0c] px-4 py-6 text-sm font-semibold text-zinc-400"
        >
          {t}
        </div>
      ))}
    </div>
  );
}

function ChartCard() {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-zinc-800 bg-[#0c0c0c] p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Pipeline overview</p>
      <div className="mt-3 h-28 rounded-xl border border-zinc-800 bg-black/60 p-3">
        <div className="flex h-full items-end gap-2">
          {[28, 38, 54, 36, 66].map((h, i) => (
            <span key={i} className="w-5 rounded-sm bg-zinc-200/90" style={{ height: `${h}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function JobsCard() {
  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-[#0c0c0c]">
      <div className="border-b border-zinc-800/80 px-4 py-3">
        <p className="text-sm font-semibold text-white">Saved roles</p>
      </div>
      <div className="space-y-2 p-4">
        {["ICU Nurse", "Warehouse Supervisor", "Secondary Math Teacher"].map((r) => (
          <div key={r} className="rounded-lg border border-zinc-800 bg-black/60 px-3 py-2 text-sm text-zinc-300">
            {r}
          </div>
        ))}
      </div>
    </div>
  );
}

function SideCard() {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-zinc-800 bg-[#0c0c0c] p-5">
      <p className="text-sm font-semibold text-white">By pipeline stage</p>
      <div className="mt-4 h-28 rounded-xl border border-zinc-800 bg-black/60 p-3">
        <div className="space-y-2">
          {[
            { label: "Saved", w: "78%" },
            { label: "Pending", w: "56%" },
            { label: "Applied", w: "68%" },
            { label: "Interview", w: "34%" },
          ].map((row) => (
            <div key={row.label} className="flex items-center gap-2 text-2xs text-zinc-400">
              <span className="w-14">{row.label}</span>
              <span className="h-1.5 flex-1 rounded-full bg-zinc-900">
                <span className="block h-full rounded-full bg-zinc-200" style={{ width: row.w }} />
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function DashboardPreview() {
  return (
    <div className="relative mx-auto max-w-6xl px-4 pb-4 sm:px-6 lg:px-8">
      <div
        className="overflow-hidden rounded-3xl border border-zinc-800 bg-black"
        style={{
          boxShadow:
            "0 -24px 80px -32px rgba(74,222,128,0.2), inset 0 1px 0 0 rgba(74,222,128,0.12)",
        }}
      >
        <div className="flex min-h-[420px] flex-col md:min-h-[480px] md:flex-row">
          <aside className="flex w-full shrink-0 flex-col border-r border-zinc-800/90 bg-[#0a0a0a] p-4 md:w-[312px]">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-100">Job Search AI</p>
            <div className="mt-4 space-y-2">
              {["Home", "My jobs", "Approvals", "Interviews"].map((item) => (
                <div
                  key={item}
                  className="rounded-md bg-zinc-900/70 px-3 py-2 text-[13px] font-medium text-zinc-300"
                >
                  {item}
                </div>
              ))}
            </div>
          </aside>
          <div className="flex min-w-0 flex-1 flex-col bg-[#050505]">
            <header className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/90 px-5 py-4">
              <div>
                <p className="text-[11px] text-zinc-500">Doubow · Home</p>
                <h2 className="text-lg font-semibold tracking-tight text-white sm:text-xl">
                  Your career workspace
                </h2>
              </div>
              <div className="flex items-center gap-2 sm:gap-3">
                <button
                  type="button"
                  className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-2 text-zinc-400 hover:text-white"
                  aria-label="Notifications"
                >
                  <Bell className="h-4 w-4" strokeWidth={1.75} />
                </button>
                <div className="hidden items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/40 px-3 py-2 sm:flex">
                  <Search className="h-4 w-4 text-zinc-500" strokeWidth={1.75} />
                  <span className="text-xs text-zinc-500">Search my jobs…</span>
                </div>
              </div>
            </header>
            <div className="space-y-4 p-4 sm:p-5">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Matches", value: "12" },
                  { label: "Queued", value: "8" },
                  { label: "Pending approvals", value: "3" },
                ].map((s) => (
                  <div key={s.label} className="rounded-xl border border-zinc-800 bg-[#0b0b0b] px-3 py-2">
                    <p className="text-2xs uppercase tracking-wide text-zinc-500">{s.label}</p>
                    <p className="mt-1 text-base font-semibold text-zinc-100">{s.value}</p>
                  </div>
                ))}
              </div>
              <div className="grid gap-4 lg:grid-cols-5">
                <div className="lg:col-span-3">
                  <ChartCard />
                </div>
                <div className="lg:col-span-2">
                  <SideCard />
                </div>
              </div>
              <div className="grid gap-4 lg:grid-cols-5">
                <div className="lg:col-span-3">
                  <JobsCard />
                </div>
                <div className="lg:col-span-2">
                  <SideCard />
                </div>
              </div>
              <BottomRow />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
