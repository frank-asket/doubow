import Link from 'next/link'

function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mx-auto max-w-5xl text-center">
      {subtitle ? (
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">{subtitle}</p>
      ) : null}
      <h2 className="mt-3 text-balance text-3xl font-semibold leading-tight tracking-[-0.02em] text-zinc-950 sm:text-4xl">
        {title}
      </h2>
    </div>
  )
}

export default function NextHireClonePage() {
  return (
    <main id="landing-main" className="min-w-0 bg-white text-zinc-950">
      <header className="sticky top-0 z-40 border-b border-zinc-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="text-lg font-bold tracking-tight">
            NextHire
          </Link>
          <nav className="hidden items-center gap-7 text-sm text-zinc-600 md:flex">
            <a href="#about" className="hover:text-zinc-950">
              About
            </a>
            <a href="#services" className="hover:text-zinc-950">
              Services
            </a>
            <a href="#how" className="hover:text-zinc-950">
              How it works
            </a>
            <a href="#testimonials" className="hover:text-zinc-950">
              Reviews
            </a>
          </nav>
          <Link
            href="/discover"
            className="rounded-full bg-zinc-950 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:-translate-y-0.5 hover:bg-zinc-800"
          >
            Contact us
          </Link>
        </div>
      </header>

      <section className="relative overflow-hidden border-b border-zinc-200">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-14 sm:px-6 sm:py-18 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-24">
          <div>
            <p className="inline-flex rounded-full border border-zinc-200 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
              Career Partner
            </p>
            <h1 className="mt-5 text-[clamp(2.7rem,7.5vw,6.2rem)] font-black uppercase leading-[0.9] tracking-[-0.04em]">
              Discover
              <br />
              Career
              <br />
              Future
            </h1>
            <p className="mt-5 max-w-md text-sm leading-relaxed text-zinc-600">
              Explore career opportunities matched perfectly to your skills, interests, and goals.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/discover"
                className="rounded-full bg-[#4f46e5] px-6 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#4338ca]"
              >
                Let&apos;s apply
              </Link>
              <a
                href="#how"
                className="rounded-full border border-zinc-300 px-6 py-3 text-sm font-semibold text-zinc-900 transition hover:bg-zinc-100"
              >
                Learn more
              </a>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-md">
            <div className="absolute -left-6 top-12 rounded-xl bg-[#4f46e5] px-3 py-2 text-xs font-semibold text-white shadow-lg">
              ★ 5.0
            </div>
            <div className="rounded-[2rem] border border-zinc-200 bg-zinc-100 p-5">
              <div className="h-[380px] rounded-[1.6rem] bg-[linear-gradient(135deg,#efefef_0%,#dddddd_40%,#f5f5f5_100%)]" />
            </div>
            <div className="absolute -right-7 bottom-10 rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-xs shadow-lg">
              <p className="font-semibold text-zinc-900">Agent Match</p>
              <p className="mt-1 text-zinc-600">+18 roles this week</p>
            </div>
          </div>
        </div>
      </section>

      <section id="about" className="border-b border-zinc-200 py-16 sm:py-24">
        <SectionTitle title="Explore Career Opportunities Matched Perfectly To Your Skills, Interests, And Goals" />
        <div className="mx-auto mt-10 grid max-w-6xl gap-6 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <article className="rounded-3xl border border-zinc-200 p-7">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">Connecting people</p>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight">With Opportunities</h3>
            <p className="mt-3 text-sm leading-relaxed text-zinc-600">
              We help people discover roles they can actually win and grow in. Every recommendation is grounded in
              skills, goals, and hiring momentum.
            </p>
          </article>
          <article className="rounded-3xl border border-zinc-200 p-7">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">Data + guidance</p>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight">Next Career Move, Clear Path</h3>
            <p className="mt-3 text-sm leading-relaxed text-zinc-600">
              From role discovery to final outreach, the platform gives you a practical step-by-step flow instead of
              endless searching.
            </p>
          </article>
        </div>
      </section>

      <section id="services" className="border-b border-zinc-200 bg-zinc-50 py-16 sm:py-24">
        <SectionTitle title="Discover World-Class Talent Ready To Elevate Your Projects To The Next Level" />
        <div className="mx-auto mt-10 grid max-w-6xl gap-6 px-4 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8">
          <div className="rounded-3xl border border-zinc-200 bg-white p-6">
            <div className="h-72 rounded-2xl bg-[linear-gradient(120deg,#e7e7e7_0%,#f7f7f7_100%)]" />
            <p className="mt-4 text-sm font-semibold">Raul Franco</p>
            <p className="text-xs text-zinc-500">Sr. Product Designer</p>
          </div>
          <div className="space-y-4 rounded-3xl border border-zinc-200 bg-white p-6">
            <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4 text-sm">
              <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">Powered by</p>
              <p className="mt-2 font-semibold">Dribbble · LinkedIn · Dice · Upwork</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-zinc-200 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">Interviews</p>
                <p className="mt-2 text-2xl font-semibold">183</p>
              </div>
              <div className="rounded-2xl border border-zinc-200 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">Offers</p>
                <p className="mt-2 text-2xl font-semibold">32</p>
              </div>
              <div className="rounded-2xl border border-zinc-200 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">Hires</p>
                <p className="mt-2 text-2xl font-semibold">12</p>
              </div>
            </div>
            <p className="text-sm leading-relaxed text-zinc-600">
              A smarter way to find jobs tailored to your needs, with verified employers and transparent requirements.
            </p>
          </div>
        </div>
      </section>

      <section id="how" className="border-b border-zinc-200 py-16 sm:py-24">
        <SectionTitle title="A Step-By-Step Guide To How Our Job Platform Works For You" />
        <div className="mx-auto mt-10 grid max-w-6xl gap-4 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
          {[
            ['01', 'Search jobs', 'Browse verified openings matched to your role and location goals.'],
            ['02', 'Apply easy', 'Generate a tailored draft, edit, approve, and send confidently.'],
            ['03', 'Get hired', 'Track responses and move to interviews with prep support.'],
          ].map(([idx, title, desc]) => (
            <article key={idx} className="rounded-3xl border border-zinc-200 bg-white p-6">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">{idx}</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight">{title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-zinc-600">{desc}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="testimonials" className="border-b border-zinc-200 bg-zinc-50 py-16 sm:py-24">
        <SectionTitle title="What Our Happy Job Seekers And Employers Are Saying" />
        <div className="mx-auto mt-10 grid max-w-6xl gap-4 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <blockquote className="rounded-3xl bg-[#4f46e5] p-7 text-white">
            <p className="text-lg leading-relaxed">
              &ldquo;I landed three interviews in two weeks because the platform made each application specific and
              easy to ship.&rdquo;
            </p>
            <footer className="mt-4 text-sm text-indigo-100">— Product designer</footer>
          </blockquote>
          <blockquote className="rounded-3xl border border-zinc-200 bg-white p-7">
            <p className="text-lg leading-relaxed text-zinc-800">
              &ldquo;The workflow is clear: search, tailor, approve, send. It removed the chaos from my job hunt.&rdquo;
            </p>
            <footer className="mt-4 text-sm text-zinc-500">— Senior frontend engineer</footer>
          </blockquote>
        </div>
      </section>

      <section className="border-b border-zinc-200 py-16 text-center sm:py-24">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">Ready to take the next step</p>
        <h2 className="mx-auto mt-3 max-w-3xl text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
          Ready To Take The Next Step In Your Career
        </h2>
        <Link
          href="/discover"
          className="mt-8 inline-flex rounded-full bg-zinc-950 px-8 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-zinc-800"
        >
          Start your journey
        </Link>
      </section>

      <footer className="bg-zinc-950 py-14 text-zinc-200">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 lg:grid-cols-[1.2fr_0.8fr_0.8fr] lg:px-8">
          <div>
            <p className="text-2xl font-semibold tracking-tight text-white">NextHire</p>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-zinc-400">
              Discover and apply to roles that fit your strengths with a practical workflow from search to offer.
            </p>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-zinc-500">Quick links</p>
            <ul className="mt-4 space-y-2 text-sm">
              <li>
                <a href="#about" className="hover:text-white">
                  About
                </a>
              </li>
              <li>
                <a href="#services" className="hover:text-white">
                  Services
                </a>
              </li>
              <li>
                <a href="#how" className="hover:text-white">
                  How it works
                </a>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-zinc-500">Contact</p>
            <ul className="mt-4 space-y-2 text-sm text-zinc-300">
              <li>Call NextHire</li>
              <li>help@nexthire.example</li>
              <li>+1 555 204 8891</li>
            </ul>
          </div>
        </div>
      </footer>
    </main>
  )
}
