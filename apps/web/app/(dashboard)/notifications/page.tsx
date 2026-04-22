import { Bell } from 'lucide-react'

const ITEMS = [
  {
    title: 'Application follow-up reminder',
    body: 'Your application for Senior Product Designer has a follow-up scheduled for tomorrow.',
    time: '2h ago',
  },
  {
    title: 'Approval required',
    body: 'A new draft is waiting in Approvals before sending.',
    time: '5h ago',
  },
  {
    title: 'Weekly summary ready',
    body: 'Your weekly discovery and pipeline summary is available.',
    time: '1d ago',
  },
]

export default function NotificationsPage() {
  return (
    <div className="space-y-5 p-5 sm:p-7">
      <header className="flex items-center gap-3">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-indigo-700">
          <Bell size={18} />
        </div>
        <div>
          <h1 className="text-[30px] font-semibold tracking-tight text-zinc-900">Notifications</h1>
          <p className="text-sm text-zinc-500">Recent alerts across your dashboard workflows.</p>
        </div>
      </header>

      <section className="rounded-[16px] border border-[#e7e8ee] bg-white p-6">
        <div className="space-y-4">
          {ITEMS.map((item) => (
            <article key={item.title} className="rounded-xl border border-zinc-100 bg-zinc-50/70 p-4">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-sm font-semibold text-zinc-900">{item.title}</h2>
                <span className="text-xs text-zinc-500">{item.time}</span>
              </div>
              <p className="mt-1 text-sm text-zinc-600">{item.body}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
