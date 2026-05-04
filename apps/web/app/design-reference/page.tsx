import type { Metadata } from 'next'
import Image from 'next/image'

export const metadata: Metadata = {
  title: 'Design reference',
  description: 'Landing and dashboard screenshot references for Doubow UI implementation.',
}

const LANDING_SHOTS = [
  { src: '/reference/landing/landing-hero.png', label: 'Hero' },
  { src: '/reference/landing/landing-dashboard-preview.png', label: 'Dashboard preview' },
  { src: '/reference/landing/landing-features-and-how-it-works.png', label: 'Features + how it works' },
  { src: '/reference/landing/landing-testimonial-and-pricing.png', label: 'Testimonials + pricing' },
  { src: '/reference/landing/landing-faq-and-cta.png', label: 'FAQ + CTA' },
  { src: '/reference/landing/landing-footer.png', label: 'Footer' },
]

const DASHBOARD_SHOTS = [
  { src: '/reference/dashboard/dashboard-discover.png', label: 'Discover' },
  { src: '/reference/dashboard/dashboard-pipeline.png', label: 'Pipeline' },
  { src: '/reference/dashboard/dashboard-approvals.png', label: 'Approvals' },
  { src: '/reference/dashboard/dashboard-interview-prep.png', label: 'Interview prep' },
  { src: '/reference/dashboard/dashboard-resume.png', label: 'Resume' },
  { src: '/reference/dashboard/dashboard-agent-status.png', label: 'Agent status' },
]

function GallerySection({
  title,
  description,
  items,
}: {
  title: string
  description: string
  items: Array<{ src: string; label: string }>
}) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-800">{title}</h2>
        <p className="text-sm text-surface-500">{description}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <article key={item.src} className="card p-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-surface-400">{item.label}</p>
            <a href={item.src} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-md border border-surface-200">
              <Image
                src={item.src}
                alt={item.label}
                width={1200}
                height={760}
                className="h-auto w-full"
                priority={item.src.endsWith('landing-hero.png')}
              />
            </a>
          </article>
        ))}
      </div>
    </section>
  )
}

const BRAND_SWATCHES = [
  { name: 'primary-green', className: 'bg-primary-green', label: '#14603B · titres / actions' },
  { name: 'secondary-green', className: 'bg-secondary-green', label: '#2EA44F · accents' },
  { name: 'primary-orange', className: 'bg-primary-orange', label: '#E89032 · titres & CTA' },
  { name: 'orange-fade', className: 'bg-orange-fade border border-border-subtle', label: '#FFF9F0 · fond carte crème' },
  { name: 'orange-muted', className: 'bg-orange-muted border border-border-subtle', label: '#FFEFD9 · pastilles sur orange' },
  { name: 'highlight-orange', className: 'bg-highlight-orange border border-border-subtle', label: '#FCE7D2 · badge / focus chaud' },
  { name: 'bg-light-green', className: 'bg-bg-light-green border border-border-subtle', label: '#EBF5EE · fond vert doux' },
] as const

function BrandColorsSection() {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-surface-800">Brand colors (GUF)</h2>
        <p className="text-sm text-surface-500">
          Tokens Tailwind : <code className="text-xs">bg-orange-fade</code>,{' '}
          <code className="text-xs">bg-orange-muted</code>, <code className="text-xs">text-primary-orange</code>, etc.
        </p>
      </div>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {BRAND_SWATCHES.map((s) => (
          <li
            key={s.name}
            className="flex items-center gap-3 rounded-lg border border-surface-200 bg-white p-3"
          >
            <div className={`h-14 w-14 shrink-0 rounded-lg ${s.className}`} aria-hidden />
            <div>
              <p className="font-mono text-xs font-semibold text-surface-800">{s.name}</p>
              <p className="text-xs text-surface-500">{s.label}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function DesignReferencePage() {
  return (
    <div className="min-h-screen bg-surface-50">
      <div className="mx-auto max-w-6xl p-6 md:p-8 space-y-8">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold text-surface-800">Design reference</h1>
          <p className="text-sm text-surface-500">
            Screenshot gallery used to build the Doubow landing page and dashboard screens.
          </p>
        </header>

        <BrandColorsSection />

        <GallerySection
          title="Landing page references"
          description="Full-page flow and section compositions."
          items={LANDING_SHOTS}
        />

        <GallerySection
          title="Dashboard references"
          description="Main app screens for discover, pipeline, approvals, and ops."
          items={DASHBOARD_SHOTS}
        />
      </div>
    </div>
  )
}
