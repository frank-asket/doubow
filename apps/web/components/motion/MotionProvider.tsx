'use client'

import { MotionConfig } from '@/lib/motion'

export default function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>
}
