'use client'

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-4 bg-[#f5faf8] px-4 py-4 dark:bg-transparent sm:px-6">
      <section className="relative flex flex-col gap-3 border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4 md:flex-row md:items-start md:justify-between">
        <div className="absolute bottom-0 left-0 top-0 w-[1.5px] bg-[#D97706]" />
        <div className="flex items-start gap-3 pl-3">
          <span className="material-symbols-outlined mt-px text-[18px] leading-none text-[#D97706]">warning</span>
          <div>
            <h2 className="text-[12px] font-semibold uppercase leading-none tracking-[0.08em] text-[#171d1c] dark:text-slate-100">Attention Required</h2>
            <p className="mt-1 text-[13px] text-[#3d4947] dark:text-slate-400">
              LinkedIn authentication has expired. Jobs requiring profile synchronization are currently paused.
            </p>
          </div>
        </div>
        <button className="inline-flex h-8 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 px-3 text-[11px] font-semibold uppercase leading-none tracking-[0.06em] text-[#00685f] dark:text-teal-400">
          Reconnect now
        </button>
      </section>

      <section className="flex flex-wrap items-end justify-between gap-3 border-b border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 pb-3">
        <div>
          <h1 className="text-[20px] font-medium leading-[1.02] tracking-[-0.01em] text-[#171d1c] dark:text-slate-100">Settings &amp; Identity</h1>
          <p className="text-[13px] text-[#6d7a77] dark:text-slate-400">Profile version: 7.0.1-hardening</p>
        </div>
        <div className="flex gap-2">
          <button className="inline-flex h-8 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 px-4 text-[12px] font-medium uppercase leading-none tracking-[0.06em] text-[#171d1c] dark:text-slate-100">
            Discard
          </button>
          <button className="inline-flex h-8 items-center justify-center border border-[0.5px] border-[#008378] bg-[#00685f] px-4 text-[12px] font-medium uppercase leading-none tracking-[0.06em] text-white">
            Save changes
          </button>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <section className="space-y-4 lg:col-span-8">
          <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
            <h3 className="mb-6 inline-flex items-center gap-2 text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
              <span className="material-symbols-outlined text-[16px]">badge</span>
              Personal Information
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Full Name</label>
                <input
                  className="h-9 w-full border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-sm leading-none outline-none focus:border-[#00685f] dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                  placeholder="Your name"
                  defaultValue=""
                />
              </div>
              <div>
                <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Preferred Title</label>
                <input
                  className="h-9 w-full border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-sm leading-none outline-none focus:border-[#00685f] dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                  placeholder="Target title"
                  defaultValue=""
                />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-[11px] uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Primary Email Address</label>
                <div className="flex gap-2">
                  <input
                    className="h-9 flex-1 border border-[0.5px] border-[rgba(188,201,198,0.9)] px-3 text-sm leading-none outline-none focus:border-[#00685f] dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                    placeholder="you@example.com"
                    defaultValue=""
                  />
                  <span className="inline-flex items-center border border-[0.5px] border-teal-200 bg-teal-50 px-2 text-[10px] font-bold uppercase tracking-[0.08em] text-[#00685f] dark:border-teal-500/40 dark:bg-teal-950/50 dark:text-teal-300">
                    Verified
                  </span>
                </div>
              </div>
            </div>
          </article>

          <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
            <h3 className="mb-6 inline-flex items-center gap-2 text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
              <span className="material-symbols-outlined text-[16px]">hub</span>
              Integration Hub
            </h3>
            <div className="space-y-3">
              <div className="flex items-start justify-between border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 p-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-[#f0f5f2] dark:border-slate-700 dark:bg-slate-800">
                    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4">
                      <path fill="#EA4335" d="M12 13.065 2.4 6.2v11.6h19.2V6.2L12 13.065Z" />
                      <path fill="#34A853" d="M21.6 6.2v11.6H2.4" />
                      <path fill="#FBBC04" d="M2.4 6.2 12 13.065 21.6 6.2 19.8 4.8H4.2Z" />
                      <path fill="#4285F4" d="M2.4 6.2v11.6h3.2V8.6Z" />
                    </svg>
                  </div>
                  <div className="pt-px">
                    <p className="text-[12px] font-semibold leading-none text-[#171d1c] dark:text-slate-100">Gmail Service</p>
                    <p className="mt-1 text-[10px] font-bold uppercase leading-none tracking-[0.08em] text-[#00685f] dark:text-teal-400">Active &amp; Syncing</p>
                  </div>
                </div>
                <button className="h-7 border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 px-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#00685f] dark:text-teal-400">
                  Reconnect
                </button>
              </div>
              <div className="flex items-start justify-between border border-[0.5px] border-amber-200 bg-amber-50/30 p-3 dark:border-amber-500/40 dark:bg-amber-950/25">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center border border-[0.5px] border-amber-200 bg-white dark:border-amber-500/40 dark:bg-slate-900">
                    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4">
                      <rect x="2" y="2" width="20" height="20" rx="3" fill="#0A66C2" />
                      <path
                        fill="#fff"
                        d="M8.52 10.06H5.9V18h2.62v-7.94ZM7.21 9c.84 0 1.37-.56 1.37-1.26-.02-.71-.53-1.25-1.35-1.25-.82 0-1.36.54-1.36 1.25 0 .7.52 1.26 1.32 1.26h.02Zm5.36 9h2.62v-4.43c0-.24.02-.47.09-.64.19-.47.62-.96 1.35-.96.95 0 1.33.72 1.33 1.77V18H20v-4.56c0-2.44-1.3-3.57-3.03-3.57-1.39 0-2 .77-2.34 1.31h.02v-1.12h-2.62c.03.72 0 7.94 0 7.94Z"
                      />
                    </svg>
                  </div>
                  <div className="pt-px">
                    <p className="text-[12px] font-semibold leading-none text-[#171d1c] dark:text-slate-100">LinkedIn Profile</p>
                    <p className="mt-1 text-[10px] font-bold uppercase leading-none tracking-[0.08em] text-[#D97706]">Re-authentication Required</p>
                  </div>
                </div>
                <button className="h-7 bg-[#00685f] px-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-white">
                  Reconnect
                </button>
              </div>
            </div>
          </article>
        </section>

        <aside className="space-y-4 lg:col-span-4">
          <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
            <h3 className="mb-6 inline-flex items-center gap-2 text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3d4947] dark:text-slate-400">
              <span className="material-symbols-outlined text-[16px]">security</span>
              Account &amp; Security
            </h3>
            <div className="space-y-4">
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-[13px] text-[#171d1c] dark:text-slate-100">Two-Factor Auth</span>
                  <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#00685f] dark:text-teal-400">Enabled</span>
                </div>
                <p className="text-[11px] text-[#3d4947] dark:text-slate-400">Using authenticator app for identity verification.</p>
              </div>
              <div className="border-t border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 pt-4">
                <button className="inline-flex h-8 w-full items-center justify-center gap-2 border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#171d1c] dark:text-slate-100">
                  <span className="material-symbols-outlined text-[14px]">download</span>
                  Request Data Export
                </button>
                <p className="mt-2 text-center text-[10px] italic text-[#6d7a77] dark:text-slate-400">Last export: 14 days ago</p>
              </div>
            </div>
          </article>

          <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-[#f8fafc] p-4 font-mono dark:border-slate-700 dark:bg-slate-800/80">
            <h4 className="mb-3 border-b border-[0.5px] border-[rgba(188,201,198,0.82)] pb-1 text-[10px] font-bold uppercase tracking-[0.08em] text-[#6d7a77] dark:border-slate-600 dark:text-slate-400">
              System Health Logs
            </h4>
            <div className="space-y-2 text-[9px]">
              <div className="flex justify-between">
                <span className="text-[#9aa7a4]">09:42:01</span>
                <span className="text-[#00685f] dark:text-teal-400">AUTH_OK</span>
              </div>
              <div className="flex justify-between bg-red-50 px-1">
                <span className="text-red-400">09:41:55</span>
                <span className="text-red-600">ERR_RATE_LIMIT</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9aa7a4]">09:41:10</span>
                <span className="text-[#00685f] dark:text-teal-400">SYNC_PARTIAL</span>
              </div>
            </div>
          </article>
        </aside>
      </div>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h5 className="text-[11px] font-bold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Current Session</h5>
            <span className="h-2 w-2 rounded-full bg-[#06b6a7]" />
          </div>
          <p className="text-lg font-bold text-[#171d1c] dark:text-slate-100">192.168.1.104</p>
          <p className="text-[12px] text-[#3d4947] dark:text-slate-400">San Francisco, CA • macOS Sonoma</p>
        </article>

        <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h5 className="text-[11px] font-bold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">API Access</h5>
            <span className="material-symbols-outlined text-[16px] text-[#6d7a77] dark:text-slate-400">key</span>
          </div>
          <p className="truncate border border-[0.5px] border-[rgba(188,201,198,0.9)] bg-[#f8fafc] px-2 py-1 font-mono text-[11px] text-[#171d1c] dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100">db_live_49102...9x22</p>
          <p className="mt-2 text-[11px] text-[#3d4947] dark:text-slate-400">Last accessed: 14m ago by Orchestrator</p>
        </article>

        <article className="border border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <h5 className="mb-4 text-[11px] font-bold uppercase tracking-[0.08em] text-[#6d7a77] dark:text-slate-400">Verification Artifacts</h5>
          <div className="flex gap-2">
            <div className="flex h-10 w-10 items-center justify-center border border-[0.5px] border-teal-200 bg-teal-50 text-[#00685f] dark:text-teal-400">
              <span className="material-symbols-outlined">badge</span>
            </div>
            <div className="flex h-10 w-10 items-center justify-center border border-[0.5px] border-[#316bf3]/40 bg-[#316bf3]/10 text-[#316bf3]">
              <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5">
                <path
                  fill="currentColor"
                  d="M12 2 4 5v6c0 5.05 3.41 9.77 8 11 4.59-1.23 8-5.95 8-11V5l-8-3Zm-1 14-3-3 1.41-1.41L11 13.17l3.59-3.59L16 11l-5 5Z"
                />
              </svg>
            </div>
          </div>
        </article>
      </section>

      <section className="border border-[0.5px] border-[#1f2937] bg-[#111827] p-4 text-white">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h4 className="mb-1 text-[12px] font-bold uppercase tracking-[0.08em] text-teal-300">Hardened Privacy Mode</h4>
            <p className="text-[12px] text-slate-300">
              Enable zero-knowledge proofs for outgoing artifacts. Raw identity data stays inside Doubow servers.
            </p>
          </div>
          <div className="flex items-center gap-3 text-[12px] font-bold uppercase tracking-[0.08em]">
            <span className="text-slate-500">Disabled</span>
            <div className="relative h-6 w-12 rounded-full bg-slate-700 p-1">
              <div className="h-4 w-4 rounded-full bg-slate-500" />
            </div>
            <span className="text-slate-600">Enabled</span>
          </div>
        </div>
      </section>

      <section className="border-t border-[0.5px] border-[rgba(188,201,198,0.9)] dark:border-slate-700 pt-4">
        <article className="flex flex-col gap-3 border border-[0.5px] border-red-300/50 bg-red-50/30 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h4 className="mb-1 text-sm font-bold text-[#ba1a1a]">Critical Account Actions</h4>
            <p className="text-[12px] text-[#3d4947] dark:text-slate-400">Purge identity graph, archive candidate profile, or deactivate account.</p>
          </div>
          <button className="inline-flex h-8 items-center justify-center border border-[0.5px] border-[#ba1a1a] px-4 text-[11px] font-semibold uppercase leading-none tracking-[0.08em] text-[#ba1a1a]">
            Deactivate Account
          </button>
        </article>
      </section>

      <style jsx global>{`
        .material-symbols-outlined {
          font-family: 'Material Symbols Outlined';
          font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 20;
          line-height: 1;
          vertical-align: middle;
        }
      `}</style>
    </div>
  )
}
