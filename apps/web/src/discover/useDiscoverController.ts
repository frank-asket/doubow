'use client'

import { useEffect, useMemo, useState } from 'react'
import type { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime'
import type { ReadonlyURLSearchParams } from 'next/navigation'
import type { JobWithScore } from '@doubow/shared'

type DiscoverSort = 'fit' | 'recent' | 'company'

function jobMatchesQuery(job: JobWithScore, q: string) {
  const needle = q.trim().toLowerCase()
  if (!needle) return true
  const hay = `${job.title} ${job.company} ${job.location ?? ''} ${job.description ?? ''}`.toLowerCase()
  return hay.includes(needle)
}

function sortJobs(items: JobWithScore[], sort: DiscoverSort): JobWithScore[] {
  if (sort === 'company') {
    return [...items].sort((a, b) => a.company.localeCompare(b.company))
  }
  if (sort === 'recent') {
    return [...items].sort(
      (a, b) => Date.parse(b.posted_at ?? b.discovered_at) - Date.parse(a.posted_at ?? a.discovered_at),
    )
  }
  return [...items].sort((a, b) => b.score.fit_score - a.score.fit_score)
}

export function useDiscoverController({
  jobs,
  minFit,
  locationFilter,
  hasSalaryOnly,
  setMinFit,
  setLocationFilter,
  setHasSalaryOnly,
  searchParams,
  router,
}: {
  jobs: JobWithScore[]
  minFit: number
  locationFilter: string
  hasSalaryOnly: boolean
  setMinFit: (value: number) => void
  setLocationFilter: (value: string) => void
  setHasSalaryOnly: (value: boolean) => void
  searchParams: ReadonlyURLSearchParams
  router: AppRouterInstance
}) {
  const [searchText, setSearchText] = useState(() => searchParams.get('q') ?? '')
  const [sortBy, setSortBy] = useState<DiscoverSort>(() => (searchParams.get('sort') as DiscoverSort) || 'fit')

  useEffect(() => {
    setSearchText(searchParams.get('q') ?? '')
    const incomingSort = (searchParams.get('sort') as DiscoverSort) || 'fit'
    setSortBy(incomingSort)
    setHasSalaryOnly(searchParams.get('has_salary') === 'true')
  }, [searchParams, setHasSalaryOnly])

  useEffect(() => {
    const trimmed = searchText.trim()
    const current = searchParams.get('q') ?? ''
    const currentSort = (searchParams.get('sort') as DiscoverSort) || 'fit'
    if (trimmed === current && currentSort === sortBy) return
    const id = window.setTimeout(() => {
      const p = new URLSearchParams(searchParams.toString())
      if (trimmed) p.set('q', trimmed)
      else p.delete('q')
      if (sortBy === 'fit') p.delete('sort')
      else p.set('sort', sortBy)
      const qs = p.toString()
      router.replace(qs ? `/discover?${qs}` : '/discover', { scroll: false })
    }, 400)
    return () => window.clearTimeout(id)
  }, [searchText, sortBy, router, searchParams])

  const fitFiltered = useMemo(
    () => jobs.filter((j) => !minFit || j.score.fit_score >= minFit),
    [jobs, minFit],
  )
  const filteredJobs = useMemo(
    () => fitFiltered.filter((j) => jobMatchesQuery(j, searchText)),
    [fitFiltered, searchText],
  )
  const sortedJobs = useMemo(() => sortJobs(filteredJobs, sortBy), [filteredJobs, sortBy])

  const minFitChip = minFit === 0 ? 'Any' : Number.isInteger(minFit) ? `${minFit}.0+` : `${minFit}+`
  const activeFilterCount =
    Number(Boolean(searchText.trim())) +
    Number(Boolean(locationFilter.trim())) +
    Number(minFit > 0) +
    Number(hasSalaryOnly)
  const precisionMode = activeFilterCount >= 2
  const highFitVisible = filteredJobs.filter((j) => j.score.fit_score >= 4).length

  const clearSearch = () => {
    setSearchText('')
    const p = new URLSearchParams(searchParams.toString())
    p.delete('q')
    const qs = p.toString()
    router.replace(qs ? `/discover?${qs}` : '/discover', { scroll: false })
  }

  const resetSearchAndFilters = () => {
    setSearchText('')
    setMinFit(0)
    setLocationFilter('')
    setSortBy('fit')
    const p = new URLSearchParams(searchParams.toString())
    p.delete('q')
    const qs = p.toString()
    router.replace(qs ? `/discover?${qs}` : '/discover', { scroll: false })
  }

  return {
    searchText,
    setSearchText,
    sortBy,
    setSortBy,
    filteredJobs,
    sortedJobs,
    minFitChip,
    precisionMode,
    highFitVisible,
    clearSearch,
    resetSearchAndFilters,
  }
}
