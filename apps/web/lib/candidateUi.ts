/**
 * Candidate Portal design tokens — driven by CSS variables on `.app-route-shell`
 * (see globals.css) so dashboard day/night toggle updates inline styles automatically.
 */
export const candidateTokens = {
  surface: 'var(--cand-surface)',
  onSurface: 'var(--cand-on-surface)',
  onVariant: 'var(--cand-on-variant)',
  outline: 'var(--cand-outline)',
  primary: 'var(--cand-primary)',
  secondary: 'var(--cand-secondary)',
  insightBlue: 'var(--cand-insight-blue)',
  primaryFixed: 'var(--cand-primary-fixed)',
  onPrimaryFixedVariant: 'var(--cand-on-primary-fixed-variant)',
  surfaceHigh: 'var(--cand-surface-high)',
  surfaceLow: 'var(--cand-surface-low)',
  amber: 'var(--cand-amber)',
} as const

/** Standard content width for candidate-hub dashboard routes */
export const candidatePageShell =
  'mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6'
