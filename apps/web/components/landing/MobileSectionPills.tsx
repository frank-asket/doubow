'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

const SECTIONS = [
  { id: 'solutions', label: 'Solutions' },
  { id: 'how-it-works', label: 'How it Works' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'faq', label: 'FAQ' },
] as const

export default function MobileSectionPills() {
  const [activeId, setActiveId] = useState<string>(SECTIONS[0].id)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mobileQuery = window.matchMedia('(max-width: 767px)')
    let observer: IntersectionObserver | null = null

    const setupObserver = () => {
      observer?.disconnect()
      observer = null
      if (!mobileQuery.matches) return

      const nodes = SECTIONS.map(({ id }) => document.getElementById(id)).filter(
        (node): node is HTMLElement => node != null,
      )
      if (nodes.length === 0) return

      observer = new IntersectionObserver(
        (entries) => {
          const visible = entries
            .filter((entry) => entry.isIntersecting)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio)
          if (visible[0]?.target?.id) {
            setActiveId(visible[0].target.id)
          }
        },
        {
          // Accounts for fixed header + mobile pill row.
          rootMargin: '-130px 0px -55% 0px',
          threshold: [0.2, 0.35, 0.5, 0.7],
        },
      )

      nodes.forEach((node) => observer?.observe(node))
    }

    setupObserver()
    mobileQuery.addEventListener('change', setupObserver)
    return () => {
      mobileQuery.removeEventListener('change', setupObserver)
      observer?.disconnect()
    }
  }, [])

  return (
    <div className="border-t border-[#c6c6cd]/70 bg-white/95 md:hidden">
      <div className="mx-auto flex max-w-7xl items-center gap-2 overflow-x-auto px-4 py-2 text-[12px]">
        {SECTIONS.map(({ id, label }) => {
          const active = activeId === id
          return (
            <a
              key={id}
              href={`#${id}`}
              aria-current={active ? 'true' : undefined}
              className={cn(
                'whitespace-nowrap rounded-full border px-3 py-1.5 font-medium transition-colors',
                active
                  ? 'border-primary-green bg-primary-green/10 text-primary-green'
                  : 'border-[#c6c6cd] bg-white text-[#45464d] hover:text-primary-green',
              )}
            >
              {label}
            </a>
          )
        })}
      </div>
    </div>
  )
}
