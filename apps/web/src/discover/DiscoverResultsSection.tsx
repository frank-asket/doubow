'use client'

import { Compass } from 'lucide-react'
import { AnimatedMetricValue } from './discoverShared'

export function DiscoverResultsSection({
  filteredCount,
  precisionMode,
  sortBy,
}: {
  filteredCount: number
  precisionMode: boolean
  sortBy: 'fit' | 'recent' | 'company'
}) {
  return (
    <div className="space-y-2 lg:col-span-8">
      <div className="flex items-center justify-between">
        <p className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
          <Compass size={13} className="text-secondary-green" />
          <AnimatedMetricValue className="min-w-[1ch]" value={String(filteredCount)} />
          {precisionMode ? ' refined matches based on your filters' : ' active opportunities found'}
        </p>
        <p className="text-xs text-zinc-600">
          Sort:{' '}
          <span className="font-semibold">
            {sortBy === 'fit' ? 'FitScore (High-Low)' : sortBy === 'recent' ? 'Most recent' : 'Company A-Z'}
          </span>
        </p>
      </div>
    </div>
  )
}
