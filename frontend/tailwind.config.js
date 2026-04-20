/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Landing-aligned emerald system (black + green)
        brand: {
          50:  '#03251A',
          100: '#064E3B',
          200: '#047857',
          400: '#34D399',
          600: '#10B981',
          800: '#A7F3D0',
          900: '#D1FAE5',
        },
        // Landing-aligned zinc neutrals for dashboard shell
        surface: {
          0:   '#000000',
          50:  '#09090B',
          100: '#111113',
          200: '#18181B',
          300: '#27272A',
          400: '#3F3F46',
          500: '#71717A',
          600: '#A1A1AA',
          700: '#D4D4D8',
          800: '#E4E4E7',
          900: '#F4F4F5',
        },
        // Semantic
        danger:  { bg: '#FCEBEB', border: '#F09595', text: '#791F1F' },
        warning: { bg: '#FAEEDA', border: '#EF9F27', text: '#633806' },
        info:    { bg: '#E6F1FB', border: '#85B7EB', text: '#0C447C' },
        purple:  { bg: '#EEEDFE', border: '#AFA9EC', text: '#3C3489' },
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'monospace'],
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
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        focus: '0 0 0 3px rgba(52,211,153,0.25)',
      },
      animation: {
        'fade-in':  'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'shimmer':  'shimmer 1.8s linear infinite',
        'spin-slow': 'spin 2s linear infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        pulseSoft: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.5' } },
        shimmer: { from: { backgroundPosition: '-200% 0' }, to: { backgroundPosition: '200% 0' } },
      },
    },
  },
  plugins: [],
}
