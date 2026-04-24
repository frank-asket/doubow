import type { ReactNode } from 'react'

type DashboardPageHeaderProps = {
  kicker?: string
  title: string
  description?: string
  actions?: ReactNode
}

/** Same title / subtitle scale as the main Dashboard overview page. */
export function DashboardPageHeader({ kicker, title, description, actions }: DashboardPageHeaderProps) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        {kicker ? (
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-zinc-500 dark:text-slate-300">{kicker}</p>
        ) : null}
        <h1 className="mt-2 text-[28px] font-bold leading-none tracking-[-0.02em] text-zinc-900 dark:text-white sm:text-[34px]">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-xl text-[15px] font-medium leading-relaxed text-zinc-500 dark:text-slate-300">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  )
}
