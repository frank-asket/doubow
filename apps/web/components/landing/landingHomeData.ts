import {
  BarChart3,
  BadgeCheck,
  Bot,
  Brain,
  Briefcase,
  CheckCircle2,
  Clock3,
  Crown,
  FileText,
  Handshake,
  Layers3,
  Rocket,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Target,
  TrendingUp,
} from 'lucide-react'

export const metrics = [
  [Clock3, 'Workflow', 'Less Time on Repetitive Tasks', 'Stop rewriting resumes and re-entering the same details for every role.'],
  [Target, 'Focus', 'Higher-Intent Applications', 'Apply to high-fit roles with tailored, role-specific materials.'],
  [BadgeCheck, 'Control', 'Human Approval on Outbound Actions', 'You stay in control: nothing is sent without your explicit review and approval.'],
] as const

export const heroSignals = [
  [Rocket, 'Launch in minutes'],
  [Layers3, 'One Assistant, full workflow'],
  [ShieldCheck, 'You approve every send'],
] as const

/** Capability pillars—all coordinated from the same Doubow Assistant chat and dashboard. */
export const capabilityCards = [
  [Search, 'Role discovery', 'Scours job boards and hidden career pages 24/7 to surface roles that match your profile.', 'Hidden Job Market Access', 'Real-time Alert System'],
  [BarChart3, 'Fit scoring', 'Scores roles based on experience, culture fit, and salary expectations before you spend time.', 'ATS Compatibility Scoring', 'Salary Range Estimation'],
  [FileText, 'Tailored materials', 'Generates role-specific resumes and cover letters in your voice with keyword precision.', 'Dynamic Bullet Pointing', 'Tone Consistency AI'],
  [Send, 'Pipeline & follow-ups', 'Tracks deadlines, prepares follow-ups, and keeps your pipeline moving forward.', 'Follow-up Sequences', 'Email Sync Integration'],
  [Brain, 'Interview prep', 'Generates practice prompts and briefing notes tailored to each company and role.', 'Practice Q&A', 'Research briefs'],
  [Handshake, 'Offer strategy', 'Benchmarks offers and provides scripts to support strong compensation conversations.', 'Market Benchmarking', 'Strategy Scripting'],
] as const

export const faqs = [
  ['How does Doubow keep my data secure?', 'We use encrypted storage and strict access controls. Your profile and drafts stay private in your workspace.'],
  ['Will recruiters know I use AI?', 'You review and approve all final outputs. Doubow assists, but you stay in control of every submission.'],
  ['What is Human-in-the-Loop?', 'AI handles repetitive prep while you own the final decisions: apply, edit, approve, and send.'],
  ['Can I cancel anytime?', 'Yes. You can change or cancel your plan from account settings without long-term lock-in.'],
] as const

export const workflowSteps = [
  { id: 'profile-sync', icon: Settings2, title: 'Profile Sync', body: 'Import your history and define your career non-negotiables once.' },
  { id: 'ai-drafts', icon: Bot, title: 'AI Drafts', body: 'Doubow surfaces roles and drafts tailored assets in the background.' },
  { id: 'human-control', icon: ShieldCheck, title: 'Human Control', body: 'You review, refine, and approve every outreach attempt.' },
  { id: 'execution', icon: CheckCircle2, title: 'Execution', body: 'Doubow tracks progress and surfaces winning opportunities.' },
] as const

export const audienceSegments = [
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

export function staggerStyle(idx: number, baseMs: number = 0) {
  return { animationDelay: `${baseMs + idx * 110}ms` }
}

export function landingCurrentYear() {
  return new Date().getFullYear()
}
