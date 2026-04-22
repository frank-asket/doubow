import LandingGateRedirect from '@/components/landing/LandingGateRedirect'
import { Benefits } from '@/components/landing/Benefits'
import { FAQ } from '@/components/landing/FAQ'
import { Footer, FooterCTA } from '@/components/landing/Footer'
import { FutureOfResumes } from '@/components/landing/FutureOfResumes'
import { Header } from '@/components/landing/Header'
import { Hero } from '@/components/landing/Hero'
import { HowItWorks } from '@/components/landing/HowItWorks'
import { PipelineShowcase } from '@/components/landing/PipelineShowcase'
import { Pricing } from '@/components/landing/Pricing'
import { ProcessStrip } from '@/components/landing/ProcessStrip'
import { Tagline } from '@/components/landing/Tagline'
import { Testimonials } from '@/components/landing/Testimonials'

export default function RootPage() {
  return (
    <div className="landing-shell">
      {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <LandingGateRedirect /> : null}
      <a
        href="#landing-main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[300] focus:rounded-lg focus:bg-zinc-100 focus:px-4 focus:py-2.5 focus:text-sm focus:font-semibold focus:text-zinc-950 focus:shadow-lg focus:outline-none"
      >
        Skip to main content
      </a>
      <main id="landing-main" className="min-w-0">
        <Header />
        <Hero />
        <Tagline />
        <Benefits />
        <PipelineShowcase />
        <HowItWorks />
        <ProcessStrip />
        <FutureOfResumes />
        <Testimonials />
        <Pricing />
        <FAQ />
        <FooterCTA />
        <Footer />
      </main>
    </div>
  )
}
