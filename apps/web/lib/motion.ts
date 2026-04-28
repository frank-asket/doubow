import {
  AnimatePresence,
  MotionConfig,
  motion,
  useReducedMotion,
  type Variants,
} from 'framer-motion'

export { AnimatePresence, MotionConfig, motion, useReducedMotion }

export const motionDurations = {
  fast: 0.16,
  normal: 0.24,
  slow: 0.36,
} as const

export const motionEasing = {
  standard: [0.22, 1, 0.36, 1] as const,
} as const

export const motionSprings = {
  snappy: { type: 'spring', stiffness: 420, damping: 30, mass: 0.8 } as const,
  smooth: { type: 'spring', stiffness: 260, damping: 26, mass: 0.95 } as const,
} as const

export const fadeInUpVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: motionDurations.normal, ease: motionEasing.standard },
  },
  exit: {
    opacity: 0,
    y: 6,
    transition: { duration: motionDurations.fast, ease: motionEasing.standard },
  },
}

export const staggerContainerVariants: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.04,
      delayChildren: 0.02,
    },
  },
  exit: {
    transition: {
      staggerChildren: 0.02,
      staggerDirection: -1,
    },
  },
}
