'use client'

import { AnimatePresence, motion, useReducedMotion } from '../../lib/motion'
import { cn } from '../../lib/utils'

export function AnimatedMetricValue({
  value,
  className,
}: {
  value: string
  className?: string
}) {
  const prefersReducedMotion = useReducedMotion()
  if (prefersReducedMotion) {
    return <span className={cn('inline-flex', className)}>{value}</span>
  }
  return (
    <span className={cn('inline-flex', className)}>
      <AnimatePresence initial={false} mode="wait">
        <motion.span
          key={value}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
        >
          {value}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}
