/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand — Guichet Unique du Foncier (GUF) aligned palette (:root in globals.css)
        'primary-green': 'var(--color-primary-green)',
        'primary-green-hover': 'var(--color-primary-green-hover)',
        'secondary-green': 'var(--color-secondary-green)',
        'primary-orange': 'var(--color-primary-orange)',
        'primary-orange-hover': 'var(--color-primary-orange-hover)',
        // UI & surfaces
        'bg-light-green': 'var(--color-bg-light-green)',
        'bg-light-orange': 'var(--color-bg-light-orange)',
        'text-main': 'var(--color-text-main)',
        'text-muted': 'var(--color-text-muted)',
        'border-subtle': 'var(--color-border-subtle)',
        'highlight-orange': 'var(--color-highlight-orange)',
        'highlight-green': 'var(--color-highlight-green)',
        /* Alias de nommage GUF (même source que ci-dessus) — ex. text-guf-green, bg-guf-green-light */
        guf: {
          green: 'var(--guf-green)',
          'green-light': 'var(--guf-green-light)',
          orange: 'var(--guf-orange)',
          'orange-light': 'var(--guf-orange-light)',
          text: 'var(--guf-text)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Georgia', 'ui-serif', 'serif'],
        mono: ['var(--font-geist-mono)', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        '2xs': ['10px', { lineHeight: '14px' }],
        xs:    ['12px', { lineHeight: '16px' }],
        sm:    ['13px', { lineHeight: '20px' }],
        base:  ['14px', { lineHeight: '22px' }],
        md:    ['15px', { lineHeight: '24px' }],
        lg:    ['16px', { lineHeight: '26px' }],
        xl:    ['18px', { lineHeight: '28px' }],
        '2xl': ['22px', { lineHeight: '32px' }],
        '3xl': ['28px', { lineHeight: '36px' }],
      },
      borderRadius: {
        sm:  '6px',
        md:  '8px',
        lg:  '12px',
        xl:  '16px',
        '2xl': '20px',
        guf: 'var(--guf-radius)',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        focus: '0 0 0 3px color-mix(in oklab, var(--color-secondary-green) 35%, transparent)',
      },
      animation: {
        'fade-in':  'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'shimmer':  'shimmer 1.8s linear infinite',
        'spin-slow': 'spin 2s linear infinite',
        'landing-rise': 'landingRise 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards',
        'landing-rise-delayed': 'landingRise 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.1s forwards',
        'landing-rise-delayed-2': 'landingRise 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.2s forwards',
      },
      keyframes: {
        landingRise: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        pulseSoft: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.5' } },
        shimmer: { from: { backgroundPosition: '-200% 0' }, to: { backgroundPosition: '200% 0' } },
      },
    },
  },
  plugins: [],
}
