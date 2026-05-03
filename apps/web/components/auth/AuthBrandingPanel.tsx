import Link from 'next/link'
import { LogoMark } from '@/components/Logo'

const highlights = [
  'Discover and score roles in one Candidate Hub',
  'Tailored drafts you review before anything goes out',
  'Interview prep grounded in the roles you pursue',
]

export function AuthBrandingPanel() {
  return (
    <aside className="relative flex flex-col justify-between overflow-hidden border-b border-slate-200/90 bg-gradient-to-b from-[#f0f5f2] to-[#f5faf8] px-8 py-10 lg:min-h-screen lg:border-b-0 lg:border-r lg:px-12 lg:py-14 dark:border-slate-800 dark:from-slate-900 dark:to-slate-950">
      <div
        className="pointer-events-none absolute inset-0 opacity-90"
        aria-hidden
      >
        <div className="absolute -right-1/4 top-12 h-72 w-72 rounded-full bg-secondary-green/15 blur-[90px]" />
        <div className="absolute bottom-8 left-0 h-56 w-56 rounded-full bg-[#FFBC01]/20 blur-[72px]" />
      </div>

      <div className="relative border-l-[3px] border-primary-green pl-5 dark:border-secondary-green">
        <Link
          href="/"
          className="inline-flex items-center gap-2.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-secondary-green"
        >
          <LogoMark className="h-9 w-9 shrink-0" />
          <span className="text-xl font-black uppercase tracking-tighter text-secondary-green dark:text-emerald-400">
            Doubow
          </span>
        </Link>
        <p className="font-display mt-10 text-2xl font-semibold leading-[1.15] tracking-[-0.02em] text-[#171d1c] dark:text-slate-100 sm:text-[1.65rem]">
          Your next role, planned and tracked — with you in control.
        </p>
        <p className="mt-4 max-w-md text-sm leading-relaxed text-[#3d4947] dark:text-slate-400">
          Create an account to track your pipeline, generate drafts that match each posting, and prep for
          interviews. Nothing sends without your approval on the real channels you use.
        </p>
        <ul className="mt-10 space-y-3">
          {highlights.map((line) => (
            <li key={line} className="flex gap-3 text-sm leading-snug text-[#2c3130] dark:text-slate-300">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary-green/12 text-primary-green dark:bg-primary-green/20 dark:text-emerald-300">
                <svg
                  className="h-3 w-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden
                >
                  <path
                    d="M20 6L9 17L4 12"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              {line}
            </li>
          ))}
        </ul>
      </div>

      <p className="relative mt-12 text-xs text-slate-500 dark:text-slate-500 lg:mt-0">
        Explore the product story on{' '}
        <Link href="/" className="font-semibold text-primary-green underline-offset-2 hover:text-primary-green hover:underline dark:text-emerald-400 dark:hover:text-emerald-300">
          the Doubow home page
        </Link>
      </p>
    </aside>
  )
}
