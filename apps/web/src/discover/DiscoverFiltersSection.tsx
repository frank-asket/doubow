'use client'

import { motion } from '../../lib/motion'
import { cn } from '../../lib/utils'
import type { Dispatch, SetStateAction } from 'react'

type MotionProps = Record<string, unknown>

export function DiscoverFiltersSection({
  locationFilter,
  setLocationFilter,
  minFit,
  setMinFit,
  setSearchText,
  setSortBy,
  microInteractionMotion,
}: {
  locationFilter: string
  setLocationFilter: (value: string) => void
  minFit: number
  setMinFit: (value: number) => void
  setSearchText: Dispatch<SetStateAction<string>>
  setSortBy: (value: 'fit' | 'recent' | 'company') => void
  microInteractionMotion: MotionProps
}) {
  return (
    <section
      className="flex flex-wrap items-center gap-2 rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 p-3"
      style={{ borderColor: 'rgba(109,122,119,0.45)' }}
    >
      <span className="px-2 text-2xs font-semibold uppercase tracking-wider text-zinc-500">Filters</span>
      <motion.button
        type="button"
        onClick={() => setLocationFilter(locationFilter.trim() ? '' : 'Remote')}
        {...microInteractionMotion}
        className={cn(
          'rounded-sm border border-[0.5px] px-3 py-1 text-xs transition-colors',
          locationFilter.trim() ? 'bg-bg-light-green text-primary-green' : 'bg-white dark:bg-slate-900 text-zinc-700 hover:bg-zinc-50',
        )}
        style={{ borderColor: 'rgba(109,122,119,0.45)' }}
      >
        Remote roles
      </motion.button>
      <motion.button
        type="button"
        onClick={() => setMinFit(minFit < 4 ? 4 : 0)}
        {...microInteractionMotion}
        className={cn(
          'rounded-sm border border-[0.5px] px-3 py-1 text-xs transition-colors',
          minFit >= 4 ? 'bg-bg-light-green text-primary-green' : 'bg-white dark:bg-slate-900 text-zinc-700 hover:bg-zinc-50',
        )}
        style={{ borderColor: 'rgba(109,122,119,0.45)' }}
      >
        High fit (4.0+)
      </motion.button>
      <motion.button
        type="button"
        onClick={() => setSearchText((s) => (s.trim() ? '' : 'full-time'))}
        {...microInteractionMotion}
        className="rounded-sm border border-[0.5px] bg-white dark:bg-slate-900 px-3 py-1 text-xs text-zinc-700 transition-colors hover:bg-zinc-50"
        style={{ borderColor: 'rgba(109,122,119,0.45)' }}
      >
        Full-time
      </motion.button>
      <motion.button
        type="button"
        onClick={() => {
          setSearchText('')
          setMinFit(0)
          setLocationFilter('')
          setSortBy('fit')
        }}
        {...microInteractionMotion}
        className="ml-auto rounded bg-primary-green px-3 py-1 text-xs font-semibold text-white transition-opacity hover:opacity-95"
      >
        Clear all
      </motion.button>
    </section>
  )
}
