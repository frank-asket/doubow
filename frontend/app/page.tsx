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
    <>
      <a
        href="#landing-main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[300] focus:rounded-lg focus:bg-emerald-400 focus:px-4 focus:py-2.5 focus:text-sm focus:font-semibold focus:text-zinc-950 focus:shadow-lg focus:outline-none"
      >
        Skip to main content
      </a>
      <Header />
      <main
        id="landing-main"
        tabIndex={-1}
        className="landing-shell bg-black [background-image:radial-gradient(900px_360px_at_50%_-80px,rgba(52,211,153,0.14),transparent_60%),linear-gradient(to_right,rgba(63,63,70,0.2)_1px,transparent_1px),linear-gradient(to_bottom,rgba(63,63,70,0.2)_1px,transparent_1px)] [background-size:auto,64px_64px,64px_64px]"
      >
        <Hero />
        <Tagline />
        <FutureOfResumes />
        <Benefits />
        <PipelineShowcase />
        <HowItWorks />
        <ProcessStrip />
        <Testimonials />
        <Pricing />
        <FAQ />
        <FooterCTA />
      </main>
      <Footer />
    </>
  )
}
