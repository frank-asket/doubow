import Link from 'next/link'
import type { Route } from 'next'
import LandingGateRedirect from '@/components/landing/LandingGateRedirect'
import LandingHomeMain from '@/components/landing/LandingHomeMain'
import MobileSectionPills from '@/components/landing/MobileSectionPills'

export default function RootPage() {
  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] selection:bg-highlight-green selection:text-primary-green">
      {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <LandingGateRedirect /> : null}
      <header className="fixed top-0 z-50 w-full border-b border-[#c6c6cd] bg-white/80 backdrop-blur-md">
        <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-8">
            <span className="font-display text-[1.35rem] font-bold tracking-[-0.03em] text-[#191c1e]">Doubow</span>
            <div className="hidden items-center gap-6 md:flex">
              <a className="border-b-2 border-primary-green pb-1 text-sm font-semibold text-primary-green" href="#solutions">Solutions</a>
              <a className="text-sm font-medium text-[#45464d] transition-colors hover:text-primary-green" href="#how-it-works">How it Works</a>
              <a className="text-sm font-medium text-[#45464d] transition-colors hover:text-primary-green" href="#pricing">Pricing</a>
              <a className="text-sm font-medium text-[#45464d] transition-colors hover:text-primary-green" href="#faq">FAQ</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link href={"/auth/sign-in" as Route} className="hidden px-4 py-2 text-[15px] font-medium text-[#45464d] transition-colors hover:text-primary-green sm:block">Sign In</Link>
            <Link href={"/auth/sign-up" as Route} className="rounded-lg bg-primary-green px-6 py-2.5 text-[15px] font-semibold text-white shadow-sm transition-[background-color,box-shadow,transform] duration-200 ease-out active:scale-[0.96] motion-reduce:active:scale-100 hover:bg-primary-green-hover hover:shadow-md">Get Started</Link>
          </div>
        </nav>
        <MobileSectionPills />
      </header>

      <main className="pt-[108px] md:pt-16">
        <LandingHomeMain />
      </main>
    </div>
  )
}
