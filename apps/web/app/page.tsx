import Link from 'next/link'
import type { Route } from 'next'
import {
  ArrowRight,
  AtSign,
  BarChart3,
  BadgeCheck,
  Bot,
  Brain,
  Briefcase,
  CheckCircle2,
  ChevronDown,
  CirclePlay,
  Clock3,
  Crown,
  FileText,
  Fingerprint,
  GitBranch,
  Globe,
  Handshake,
  Layers3,
  Quote,
  Rocket,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'
import LandingGateRedirect from '@/components/landing/LandingGateRedirect'
import { Pricing as LegacyPricing } from '@/components/landing/Pricing'

const metrics = [
  [Clock3, '85%', 'Less Time on Repetitive Tasks', 'Stop rewriting resumes and re-entering the same details for every role.'],
  [Target, '3.4x', 'More Qualified Interviews', 'Apply only to high-fit roles with tailored, role-specific materials.'],
  [BadgeCheck, '50k+', 'Professionals Using Doubow', 'From ambitious operators to executives running focused job searches.'],
] as const

const heroSignals = [
  [Rocket, 'Launch in minutes'],
  [Layers3, 'One Assistant, full workflow'],
  [ShieldCheck, 'You approve every send'],
] as const

/** Capability pillars—all coordinated from the same Doubow Assistant chat and dashboard. */
const capabilityCards = [
  [Search, 'Role discovery', 'Scours job boards and hidden career pages 24/7 to surface roles that match your profile.', 'Hidden Job Market Access', 'Real-time Alert System'],
  [BarChart3, 'Fit scoring', 'Scores roles based on experience, culture fit, and salary expectations before you spend time.', 'ATS Compatibility Scoring', 'Salary Range Estimation'],
  [FileText, 'Tailored materials', 'Generates role-specific resumes and cover letters in your voice with keyword precision.', 'Dynamic Bullet Pointing', 'Tone Consistency AI'],
  [Send, 'Pipeline & follow-ups', 'Tracks deadlines, prepares follow-ups, and keeps your pipeline moving forward.', 'Follow-up Sequences', 'Email Sync Integration'],
  [Brain, 'Interview prep', 'Generates practice prompts and briefing notes tailored to each company and role.', 'Practice Q&A', 'Research briefs'],
  [Handshake, 'Offer strategy', 'Benchmarks offers and provides scripts to support strong compensation conversations.', 'Market Benchmarking', 'Strategy Scripting'],
] as const

const faqs = [
  ['How does DouBow keep my data secure?', 'We use encrypted storage and strict access controls. Your profile and drafts stay private in your workspace.'],
  ['Will recruiters know I use AI?', 'You review and approve all final outputs. DouBow assists, but you stay in control of every submission.'],
  ['What is Human-in-the-Loop?', 'AI handles repetitive prep while you own the final decisions: apply, edit, approve, and send.'],
  ['Can I cancel anytime?', 'Yes. You can change or cancel your plan from account settings without long-term lock-in.'],
] as const

const workflowSteps = [
  { id: 'profile-sync', icon: Settings2, title: 'Profile Sync', body: 'Import your history and define your career non-negotiables once.' },
  { id: 'ai-drafts', icon: Bot, title: 'AI Drafts', body: 'Doubow surfaces roles and drafts tailored assets in the background.' },
  { id: 'human-control', icon: ShieldCheck, title: 'Human Control', body: 'You review, refine, and approve every outreach attempt.' },
  { id: 'execution', icon: CheckCircle2, title: 'Execution', body: 'DouBow tracks progress and surfaces winning opportunities.' },
] as const

const audienceSegments = [
  {
    id: 'entry-level',
    icon: Briefcase,
    label: 'Entry-Level',
    headline: 'Break in faster without guessing what recruiters want.',
    pain: 'You are applying broadly but getting few interviews because your resume and outreach are not role-specific yet.',
    outcome: 'Doubow helps you target the right roles, tailor every application, and build confidence with structured interview prep.',
    cta: 'Launch your first targeted search',
  },
  {
    id: 'mid-level',
    icon: TrendingUp,
    label: 'Mid-Level',
    headline: 'Level up with focused applications, not extra hours.',
    pain: 'You have strong experience, but job search becomes a second full-time job when balancing work, family, and applications.',
    outcome: 'Doubow automates discovery, personalization, and tracking so you can focus on high-leverage decisions.',
    cta: 'Run a smarter weekly pipeline',
  },
  {
    id: 'executive',
    icon: Crown,
    label: 'Executive',
    headline: 'Pursue high-stakes roles with precision and discretion.',
    pain: 'At senior levels, random outreach and generic materials dilute your positioning and waste valuable opportunities.',
    outcome: 'Doubow prioritizes strategic-fit roles, sharpens executive narratives, and supports high-quality interview readiness.',
    cta: 'Start an executive-grade search',
  },
] as const

const staggerStyle = (idx: number, baseMs: number = 0) => ({
  animationDelay: `${baseMs + idx * 110}ms`,
})

export default function RootPage() {
  return (
    <div className="bg-[#f7f9fb] text-[#191c1e] selection:bg-[#86f2e4]/60 selection:text-[#006f66]">
      {process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? <LandingGateRedirect /> : null}
      <header className="fixed top-0 z-50 w-full border-b border-[#c6c6cd] bg-white/80 backdrop-blur-md">
        <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-8">
            <span className="font-display text-[1.35rem] font-bold tracking-[-0.03em] text-[#191c1e]">DouBow</span>
            <div className="hidden items-center gap-6 md:flex">
              <a className="border-b-2 border-[#006a61] pb-1 text-sm font-semibold text-[#006a61]" href="#solutions">Solutions</a>
              <a className="text-sm font-medium text-[#45464d] transition-colors hover:text-[#006a61]" href="#how-it-works">How it Works</a>
              <a className="text-sm font-medium text-[#45464d] transition-colors hover:text-[#006a61]" href="#pricing">Pricing</a>
              <a className="text-sm font-medium text-[#45464d] transition-colors hover:text-[#006a61]" href="#faq">FAQ</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link href={"/auth/sign-in" as Route} className="hidden px-4 py-2 text-[15px] font-medium text-[#45464d] transition-colors hover:text-[#006a61] sm:block">Sign In</Link>
            <Link href={"/auth/sign-up" as Route} className="rounded-lg bg-[#006a61] px-6 py-2.5 text-[15px] font-semibold text-white transition-all hover:bg-[#005049] hover:shadow-md">Get Started</Link>
          </div>
        </nav>
      </header>

      <main className="pt-16">
        <section className="relative overflow-hidden pb-[96px] pt-[80px]">
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute -left-16 top-16 h-64 w-64 rounded-full bg-[#86f2e4]/25 blur-3xl motion-safe:animate-pulse" />
            <div className="absolute right-0 top-0 h-72 w-72 rounded-full bg-[#8f95ff]/20 blur-3xl motion-safe:animate-pulse" />
            <div className="absolute bottom-0 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-[#006a61]/10 blur-3xl" />
          </div>
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto mb-16 max-w-3xl text-center motion-safe:animate-landing-rise motion-reduce:animate-none">
              <span className="mb-6 inline-block rounded-full bg-[#e1e0ff] px-3 py-1 text-[12px] font-semibold uppercase tracking-[0.05em] text-[#2f2ebe]">AI-DRIVEN CAREER CO-PILOT</span>
              <h1 className="font-display mb-6 text-[clamp(2.5rem,5vw,3rem)] font-bold leading-[1.18] tracking-[-0.02em] text-[#000000]">Stop wasting hours on job applications. <span className="text-[#006a61]">Focus only on the right roles.</span></h1>
              <p className="mb-10 text-[18px] leading-[1.6] text-[#45464d]">Doubow Assistant is your AI career copilot for modern job search: it finds high-fit roles, tailors your resume and outreach, and tracks every application in one place. You approve every final action.</p>
              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link href={"/auth/sign-up" as Route} className="inline-flex h-14 w-full items-center justify-center rounded-[8px] bg-[#006a61] px-8 text-center text-[15px] font-semibold text-white shadow-lg transition-all hover:bg-[#005049] hover:shadow-xl sm:w-auto">Start Free and See Your Matches</Link>
                <a href="#how-it-works" className="inline-flex h-14 w-full items-center justify-center gap-2 rounded-[8px] border border-[#c6c6cd] bg-white px-8 text-center text-[15px] font-semibold text-[#191c1e] transition-all hover:bg-[#f2f4f6] sm:w-auto">
                  <CirclePlay className="h-5 w-5" />
                  See how it works
                </a>
              </div>
              <div className="mt-7 flex flex-wrap items-center justify-center gap-2.5">
                {heroSignals.map(([Icon, label], idx) => (
                  <span
                    key={label}
                    className="inline-flex items-center gap-2 rounded-full border border-[#c6c6cd] bg-white/85 px-3 py-1.5 text-[12px] font-medium leading-none text-[#45464d] opacity-0 shadow-sm transition-transform duration-200 hover:-translate-y-0.5 motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100"
                    style={staggerStyle(idx, 140)}
                  >
                    <Icon className="h-3.5 w-3.5 text-[#006a61]" />
                    {label}
                  </span>
                ))}
              </div>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-2 text-[12px]">
                <a href="#solutions" className="rounded-full border border-[#c6c6cd] bg-white px-3 py-1.5 font-medium text-[#45464d] transition-colors hover:border-[#98ddd2] hover:text-[#006a61]">Explore capabilities</a>
                <a href="#how-it-works" className="rounded-full border border-[#c6c6cd] bg-white px-3 py-1.5 font-medium text-[#45464d] transition-colors hover:border-[#98ddd2] hover:text-[#006a61]">See Workflow</a>
                <a href="#pricing" className="rounded-full border border-[#c6c6cd] bg-white px-3 py-1.5 font-medium text-[#45464d] transition-colors hover:border-[#98ddd2] hover:text-[#006a61]">Compare Pricing</a>
              </div>
            </div>

            <div className="relative mx-auto max-w-5xl overflow-hidden rounded-xl border border-[#c6c6cd] bg-white shadow-2xl shadow-[#7073ff]/15 transition-transform duration-300 hover:-translate-y-0.5 motion-safe:animate-landing-rise-delayed motion-reduce:animate-none">
              <div className="flex items-center justify-between border-b border-[#c6c6cd] bg-[#e6e8ea] px-4 py-3">
                <div className="flex gap-2">
                  <div className="h-3 w-3 rounded-full bg-[#ffdad6]" />
                  <div className="h-3 w-3 rounded-full bg-[#6bd8cb]" />
                  <div className="h-3 w-3 rounded-full bg-[#7c839b]/50" />
                </div>
                <div className="rounded bg-white/80 px-4 py-1 text-xs text-[#45464d]">doubow.ai/dashboard/overview</div>
                <div className="w-12" />
              </div>
              <div className="grid gap-4 p-6 md:grid-cols-3">
                <div className="rounded-lg border border-[#c6c6cd] bg-[#f2f4f6] p-4 transition-all duration-200 hover:border-[#98ddd2] hover:shadow-sm">
                  <p className="text-xs uppercase tracking-wider text-[#45464d]">High-fit roles found</p>
                  <p className="mt-2 text-2xl font-bold text-[#191c1e]">24</p>
                </div>
                <div className="rounded-lg border border-[#c6c6cd] bg-[#f2f4f6] p-4 transition-all duration-200 hover:border-[#98ddd2] hover:shadow-sm">
                  <p className="text-xs uppercase tracking-wider text-[#45464d]">Interview pipeline</p>
                  <p className="mt-2 text-2xl font-bold text-[#191c1e]">8 active</p>
                </div>
                <div className="rounded-lg border border-[#c6c6cd] bg-[#f2f4f6] p-4 transition-all duration-200 hover:border-[#98ddd2] hover:shadow-sm">
                  <p className="text-xs uppercase tracking-wider text-[#45464d]">Average fit score</p>
                  <p className="mt-2 text-2xl font-bold text-[#191c1e]">4.3/5</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-[#c6c6cd]/40 bg-[#f2f4f6] py-[80px]">
          <div className="mx-auto grid max-w-7xl grid-cols-1 gap-8 px-4 text-center sm:px-6 md:grid-cols-3 lg:px-8">
            {metrics.map(([Icon, metric, title, sub], idx) => (
              <div
                key={title}
                className="flex h-full flex-col items-center rounded-2xl border border-[#c6c6cd]/30 bg-white p-6 text-center opacity-0 shadow-sm motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100"
                style={staggerStyle(idx, 40)}
              >
                <div className="mx-auto mb-4 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[#86f2e4]/35 text-[#006f66]">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="font-display text-[48px] leading-[1.2] tracking-[-0.02em] text-[#006a61]">{metric}</div>
                <div className="mt-2 text-[12px] font-semibold uppercase tracking-[0.05em] text-[#45464d]">{title}</div>
                <p className="mt-2 text-[14px] leading-[1.45] text-[#45464d]/80">{sub}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="solutions" className="py-[80px]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-14 text-center">
              <span className="inline-flex items-center gap-2 rounded-full border border-[#c6c6cd] bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.05em] text-[#006a61]">
                <Sparkles className="h-3.5 w-3.5" />
                Doubow Assistant
              </span>
              <h2 className="font-display text-[36px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#000000]">How Doubow solves your search bottlenecks</h2>
              <p className="mx-auto mt-4 max-w-2xl text-[16px] leading-[1.5] text-[#45464d]">One Assistant and one workspace cover discovery through negotiation—so you move faster without juggling separate tools or chats.</p>
            </div>
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
              {capabilityCards.map(([Icon, title, body, p1, p2], idx) => (
                <article
                  key={title}
                  className="group flex h-full flex-col rounded-xl border border-[#c6c6cd] bg-white p-8 opacity-0 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-[#98ddd2] hover:shadow-lg motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100"
                  style={staggerStyle(idx, 70)}
                >
                  <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-lg bg-[#86f2e4]/35 text-[#006f66] transition-transform group-hover:scale-110">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[#f2f4f6] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.04em] text-[#45464d]">
                    {String(idx + 1).padStart(2, '0')} · Capability
                  </div>
                  <h3 className="mb-3 text-[24px] font-semibold leading-[1.3] text-[#000000]">{title}</h3>
                  <p className="mb-6 text-[16px] leading-[1.5] text-[#45464d]">{body}</p>
                  <ul className="mt-auto space-y-3 text-[14px] leading-[1.4] text-[#191c1e]">
                    <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#006a61]" /> <span>{p1}</span></li>
                    <li className="flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#006a61]" /> <span>{p2}</span></li>
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="border-y border-[#c6c6cd]/40 bg-white py-[80px]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-12 text-center">
              <span className="inline-flex items-center gap-2 rounded-full border border-[#c6c6cd] bg-[#f7f9fb] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.05em] text-[#2f2ebe]">
                <Target className="h-3.5 w-3.5" />
                Audience Fit
              </span>
              <h2 className="font-display text-[36px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#000000]">Messaging built for your career stage</h2>
              <p className="mx-auto mt-4 max-w-3xl text-[16px] leading-[1.5] text-[#45464d]">Whether you are breaking in, stepping up, or targeting executive leadership, Doubow adapts the workflow to your goals.</p>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {audienceSegments.map((segment, idx) => (
                <article
                  key={segment.id}
                  className="flex h-full flex-col rounded-xl border border-[#c6c6cd] bg-[#f7f9fb] p-6 opacity-0 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-[#98ddd2] hover:shadow-md motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100"
                  style={staggerStyle(idx, 60)}
                >
                  <span className="mb-4 inline-flex w-fit items-center gap-1.5 rounded-full bg-[#e1e0ff] px-3 py-1 text-[12px] font-semibold uppercase tracking-[0.05em] text-[#2f2ebe]">
                    <segment.icon className="h-3.5 w-3.5" />
                    {segment.label}
                  </span>
                  <h3 className="text-[24px] font-semibold leading-[1.3] text-[#000000]">{segment.headline}</h3>
                  <p className="mt-4 text-[15px] leading-[1.55] text-[#45464d]">
                    <span className="font-semibold text-[#191c1e]">The problem: </span>
                    {segment.pain}
                  </p>
                  <p className="mt-3 text-[15px] leading-[1.55] text-[#45464d]">
                    <span className="font-semibold text-[#191c1e]">How Doubow helps: </span>
                    {segment.outcome}
                  </p>
                  <Link
                    href={"/auth/sign-up" as Route}
                    className="mt-auto inline-flex h-11 items-center justify-center rounded-[8px] bg-[#006a61] px-4 text-[15px] font-semibold text-white transition-colors hover:bg-[#005049]"
                  >
                    {segment.cta}
                  </Link>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="how-it-works" className="bg-[#f7f9fb] py-[80px]">
          <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-16 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
            <div>
              <span className="mb-4 block text-[12px] font-semibold uppercase tracking-[0.05em] text-[#006a61]">THE ENGINE UNDER THE HOOD</span>
              <h2 className="font-display mb-6 text-[36px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#000000]">Built for real job seekers, not generic AI chat</h2>
              <p className="mb-8 text-[18px] leading-[1.6] text-[#45464d]">Doubow Assistant is purpose-built for job search: one conversation for roles, pipeline, resume, drafts, and prep—with orchestration under the hood so nothing falls through the cracks.</p>
              <div className="space-y-5 text-sm text-[#191c1e]">
                <div className="rounded-xl border border-transparent p-4 opacity-0 transition-all duration-300 hover:-translate-y-0.5 hover:border-[#c6c6cd] hover:bg-white motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100" style={staggerStyle(0, 80)}><strong className="inline-flex items-center gap-2"><GitBranch className="h-4 w-4 text-[#006a61]" /> Semantic Matching Engine</strong><p className="mt-1 text-[#45464d]">Understands context, seniority, and requirements beyond keyword matching.</p></div>
                <div className="rounded-xl border border-transparent p-4 opacity-0 transition-all duration-300 hover:-translate-y-0.5 hover:border-[#c6c6cd] hover:bg-white motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100" style={staggerStyle(1, 80)}><strong className="inline-flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-[#006a61]" /> Privacy-First Data Vault</strong><p className="mt-1 text-[#45464d]">Encrypted storage with strict permissions and explicit user approval controls.</p></div>
                <div className="rounded-xl border border-transparent p-4 opacity-0 transition-all duration-300 hover:-translate-y-0.5 hover:border-[#c6c6cd] hover:bg-white motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100" style={staggerStyle(2, 80)}><strong className="inline-flex items-center gap-2"><Sparkles className="h-4 w-4 text-[#006a61]" /> Human-in-the-Loop Protocol</strong><p className="mt-1 text-[#45464d]">All external actions require your final review and explicit confirmation.</p></div>
              </div>
            </div>
            <div className="relative rounded-3xl border border-[#c6c6cd] bg-white p-8 shadow-xl transition-transform duration-300 hover:-translate-y-1">
              <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-[#006a61]/10 blur-2xl" />
              <div className="absolute -bottom-8 -left-6 h-28 w-28 rounded-full bg-[#565e74]/10 blur-3xl" />
              <div className="space-y-4 text-sm">
                <div className="flex items-center justify-between rounded-lg border border-[#c6c6cd]/40 bg-[#f2f4f6] p-4 opacity-0 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-sm motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100" style={staggerStyle(0, 90)}><span className="inline-flex items-center gap-2"><div className="inline-flex h-6 w-6 items-center justify-center rounded bg-[#006a61] text-[10px] font-bold text-white">1</div> Assistant · Scanning boards & LinkedIn…</span><span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700">ACTIVE</span></div>
                <div className="flex items-center justify-between rounded-lg border border-[#c6c6cd]/40 bg-[#f2f4f6] p-4 opacity-0 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-sm motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100" style={staggerStyle(1, 90)}><span className="inline-flex items-center gap-2"><div className="inline-flex h-6 w-6 items-center justify-center rounded bg-[#000000] text-[10px] font-bold text-white">2</div> Evaluating a posted role against your profile</span><span className="rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-700">SCORING</span></div>
                <div className="flex items-center justify-between rounded-lg border border-[#c6c6cd]/40 bg-[#f2f4f6] p-4 opacity-0 transition-all duration-200 hover:-translate-y-0.5 hover:opacity-100 hover:shadow-sm motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100" style={staggerStyle(2, 90)}><span className="inline-flex items-center gap-2"><div className="inline-flex h-6 w-6 items-center justify-center rounded bg-slate-400 text-[10px] font-bold text-white">3</div> Drafting tailored resume…</span><span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-600">QUEUED</span></div>
              </div>
              <div className="mt-8 border-t border-[#c6c6cd] pt-6">
                <p className="text-xs font-bold uppercase tracking-widest text-[#45464d]">User approval required</p>
                <p className="mt-1 inline-flex items-center gap-2 font-semibold text-[#191c1e]"><Fingerprint className="h-4 w-4 text-[#006a61]" /> Approve outbound draft before it sends?</p>
                <div className="mt-4 flex gap-2">
                  <button className="flex h-11 flex-1 items-center justify-center rounded-[8px] bg-[#006a61] text-[15px] font-semibold text-white transition-colors hover:bg-[#005049]">Approve</button>
                  <button className="flex h-11 flex-1 items-center justify-center rounded-[8px] border border-[#c6c6cd] bg-white text-[15px] font-semibold text-[#191c1e] transition-colors hover:bg-[#f2f4f6]">Edit Draft</button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="overflow-hidden bg-[#131b2e] py-[80px] text-white">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-20 text-center">
              <h2 className="font-display text-[36px] font-semibold leading-[1.2] tracking-[-0.01em]">From overwhelm to a clear weekly plan</h2>
              <p className="mx-auto mt-4 max-w-xl text-[16px] leading-[1.5] text-slate-300">Doubow turns chaotic job search into a repeatable system you can run confidently.</p>
            </div>
            <div className="relative grid grid-cols-1 gap-12 md:grid-cols-2 lg:grid-cols-4">
              <div className="pointer-events-none absolute left-0 right-0 top-8 hidden h-px bg-gradient-to-r from-transparent via-slate-600 to-transparent lg:block" />
              {workflowSteps.map(({ id, icon: StepIcon, title, body }, idx) => {
                return (
                  <div
                    key={id}
                    className="flex flex-col items-center text-center opacity-0 motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100"
                    style={staggerStyle(idx, 70)}
                  >
                    <div className="relative mb-6 flex h-16 w-16 items-center justify-center rounded-full border-2 border-slate-700 bg-slate-800 shadow-lg shadow-black/20">
                      <StepIcon className="h-6 w-6 text-[#86f2e4]" />
                      <span className="absolute -right-1 -top-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#006a61] text-xs font-bold text-white">{idx + 1}</span>
                    </div>
                    <h4 className="text-lg font-semibold">{title}</h4>
                    <p className="mt-2 text-sm text-slate-400">{body}</p>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <LegacyPricing />

        <section id="faq" className="bg-white py-[80px]">
          <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
            <div className="mb-12 text-center">
              <h2 className="font-display text-[36px] font-semibold leading-[1.2] tracking-[-0.01em] text-[#000000]">Frequently Asked Questions</h2>
              <p className="mt-4 text-[#45464d]">Quick answers about trust, control, and how Doubow fits into your search.</p>
            </div>
            <div className="space-y-4">
              {faqs.map(([q, a], idx) => (
                <details
                  key={q}
                  className="group rounded-xl border border-[#c6c6cd] bg-white p-5 opacity-0 transition-all duration-200 hover:border-[#98ddd2] motion-safe:animate-landing-rise motion-reduce:animate-none motion-reduce:opacity-100"
                  style={staggerStyle(idx, 50)}
                >
                  <summary className="flex cursor-pointer list-none items-start justify-between gap-3 font-semibold text-[#191c1e]">{q}<ChevronDown className="mt-0.5 h-4 w-4 flex-shrink-0 transition-transform duration-300 group-open:rotate-180" /></summary>
                  <p className="mt-3 text-sm leading-[1.55] text-[#45464d]">{a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-[#c6c6cd]/40 bg-white py-[80px]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="rounded-3xl bg-[#86f2e4]/20 p-10 md:p-16">
              <div className="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
                <div className="max-w-md">
                  <h3 className="text-[24px] font-semibold leading-[1.3] text-[#000000]">Get Weekly Career Insights</h3>
                  <p className="mt-3 text-[#45464d]">Get practical job-search playbooks, hiring trend breakdowns, and proven tactics you can use immediately.</p>
                </div>
                <form className="w-full max-w-sm space-y-3">
                  <input type="email" placeholder="Enter your email" className="w-full rounded-lg border border-[#c6c6cd] px-4 py-3 text-sm outline-none transition focus:border-[#006a61] focus:ring-2 focus:ring-[#006a61]/20" />
                  <button type="button" className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-[8px] bg-[#006a61] px-6 text-[15px] font-semibold text-white transition-colors hover:bg-[#005049]">Subscribe <ArrowRight className="h-4 w-4" /></button>
                </form>
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-[#c6c6cd] py-[80px]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <p className="mb-10 text-center text-[12px] font-semibold uppercase tracking-[0.05em] text-[#45464d]">Trusted by talent from leading companies</p>
            <div className="flex flex-wrap justify-center gap-10 text-2xl font-semibold tracking-wide text-[#45464d]/60">
              <span>GOOGLE</span><span>STRIPE</span><span>META</span><span>AIRBNB</span><span>ADOBE</span>
            </div>
            <div className="mx-auto mt-20 max-w-4xl rounded-2xl bg-[#eceef0] p-10 md:p-12">
              <Quote className="h-10 w-10 text-[#006a61]/35" />
              <p className="mt-5 text-[24px] italic leading-[1.35] text-[#191c1e]">&quot;DouBow transformed my job search into a precise operation. I landed a Senior Director role in three weeks while spending only 30 minutes a day.&quot;</p>
              <p className="mt-5 text-sm font-semibold text-[#191c1e]">Marcus Chen · Senior Director of Engineering</p>
            </div>
          </div>
        </section>

        <section className="py-[80px]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="relative overflow-hidden rounded-3xl bg-[#131b2e] p-12 text-center text-white md:p-20">
              <div className="absolute right-0 top-0 h-full w-1/3 translate-x-1/2 skew-x-12 bg-[#86f2e4]/10" />
              <div className="absolute -left-8 -top-8 h-32 w-32 rounded-full bg-[#86f2e4]/15 blur-2xl" />
              <h2 className="font-display relative z-10 text-[36px] font-semibold leading-[1.2] tracking-[-0.01em]">Ready to stop guessing and start landing better roles?</h2>
              <p className="relative z-10 mx-auto mt-5 max-w-2xl text-[18px] leading-[1.6] text-[#7c839b]">Create your profile, get your first high-fit matches, and review AI-tailored drafts in minutes.</p>
              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link href={"/auth/sign-up" as Route} className="relative z-10 inline-flex h-14 items-center justify-center rounded-[8px] bg-[#006a61] px-10 text-[15px] font-semibold text-white transition-colors hover:bg-[#005049]">Get Started for Free</Link>
                <button className="relative z-10 inline-flex h-14 items-center justify-center rounded-[8px] border border-white/20 px-10 text-[15px] font-semibold text-white transition-colors hover:bg-white/10">Contact sales</button>
              </div>
            </div>
          </div>
        </section>

        <footer className="border-t border-[#c6c6cd] bg-slate-50 pb-8 pt-16 dark:border-slate-800 dark:bg-slate-900">
          <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-4 sm:px-6 md:grid-cols-4 lg:grid-cols-5 lg:px-8">
            <div className="col-span-2 lg:col-span-1">
              <span className="mb-4 block text-lg font-bold text-slate-900 dark:text-white">DouBow</span>
              <p className="text-sm text-slate-500 dark:text-slate-400">Precision in Career Growth. One Assistant that works with you across discovery, applications, and prep—without the noise of generic chat.</p>
              <div className="mt-4 flex gap-3 text-slate-400 dark:text-slate-500">
                <Globe className="h-4 w-4" />
                <AtSign className="h-4 w-4" />
              </div>
            </div>
            <div><h4 className="mb-4 text-xs font-semibold uppercase tracking-[0.05em] text-slate-700 dark:text-slate-200">Product</h4><ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400"><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Features</li><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Pricing</li><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Resume AI</li></ul></div>
            <div><h4 className="mb-4 text-xs font-semibold uppercase tracking-[0.05em] text-slate-700 dark:text-slate-200">Company</h4><ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400"><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">About</li><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Careers</li><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Contact</li></ul></div>
            <div><h4 className="mb-4 text-xs font-semibold uppercase tracking-[0.05em] text-slate-700 dark:text-slate-200">Legal</h4><ul className="space-y-3 text-sm text-slate-500 dark:text-slate-400"><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Privacy</li><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Terms</li><li className="transition-colors hover:text-slate-900 dark:hover:text-slate-200">Security</li></ul></div>
          </div>
          <div className="mx-auto mt-14 max-w-7xl border-t border-slate-200 px-4 pt-8 sm:px-6 lg:px-8 dark:border-slate-800">
            <p className="text-center text-sm text-slate-500 dark:text-slate-400">© 2024 DouBow AI. Precision in Career Growth.</p>
          </div>
        </footer>
      </main>
    </div>
  )
}
