import Link from 'next/link'
import type { Metadata } from 'next'
import type { Route } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service | Doubow',
  description: 'Terms that govern your use of Doubow services.',
}

const lastUpdated = 'April 29, 2026'

export default function TermsOfServicePage() {
  return (
    <main className="min-h-screen bg-[#f7f9fb] text-[#191c1e]">
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <Link
          href={"/" as Route}
          className="inline-flex items-center rounded-[8px] border border-[#c6c6cd] bg-white px-3 py-1.5 text-sm font-medium text-[#45464d] transition-colors hover:bg-[#f2f4f6]"
        >
          Back to home
        </Link>

        <header className="mt-8 rounded-2xl border border-[#c6c6cd] bg-white p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-[#006a61]">Legal</p>
          <h1 className="mt-3 font-display text-4xl font-semibold tracking-[-0.02em] text-[#000000]">Terms of Service</h1>
          <p className="mt-4 text-[16px] leading-[1.6] text-[#45464d]">
            These Terms govern your access to and use of Doubow products and services.
          </p>
          <p className="mt-4 text-sm text-[#45464d]">Last updated: {lastUpdated}</p>
        </header>

        <section className="mt-8 space-y-6 rounded-2xl border border-[#c6c6cd] bg-white p-8 shadow-sm">
          <TermsSection
            title="1) Acceptance of terms"
            items={[
              'By accessing or using Doubow, you agree to these Terms and our Privacy Policy.',
              'If you use Doubow on behalf of an organization, you represent that you have authority to bind that organization.',
            ]}
          />

          <TermsSection
            title="2) Eligibility and accounts"
            items={[
              'You must provide accurate account information and keep credentials secure.',
              'You are responsible for activity under your account, whether authorized by you or not.',
              'You must promptly notify us of unauthorized account use.',
            ]}
          />

          <TermsSection
            title="3) Use of the service"
            items={[
              'You may use Doubow only in compliance with applicable law and these Terms.',
              'You agree not to misuse the platform, interfere with service operation, or attempt unauthorized access.',
              'You are responsible for reviewing and approving outputs before external use or sending.',
            ]}
          />

          <TermsSection
            title="4) User content and permissions"
            items={[
              'You retain ownership of content you provide to Doubow (such as resumes, drafts, and preferences).',
              'You grant Doubow a limited license to process your content solely to provide and improve the service.',
              'You represent that you have rights to submit the content you upload.',
            ]}
          />

          <TermsSection
            title="5) Plans, billing, and cancellation"
            items={[
              'Paid plans are billed according to your selected billing cycle and plan terms.',
              'Unless otherwise stated, subscriptions renew automatically until cancelled.',
              'You may cancel future renewals at any time from account settings.',
              'Fees already paid are generally non-refundable except where required by law.',
            ]}
          />

          <TermsSection
            title="6) Intellectual property"
            items={[
              'Doubow and its associated software, branding, and materials are protected by intellectual property laws.',
              'Except as expressly permitted, you may not copy, reverse engineer, distribute, or create derivative works from the service.',
            ]}
          />

          <TermsSection
            title="7) Disclaimers"
            items={[
              'Doubow is provided on an “as is” and “as available” basis to the extent permitted by law.',
              'We do not guarantee specific hiring outcomes, interview offers, or compensation results.',
              'You are responsible for final decisions and actions taken based on service outputs.',
            ]}
          />

          <TermsSection
            title="8) Limitation of liability"
            items={[
              'To the maximum extent permitted by law, Doubow will not be liable for indirect, incidental, special, consequential, or punitive damages.',
              'Our total liability for claims arising out of or related to the service is limited to amounts paid by you for the service in the period specified by applicable law.',
            ]}
          />

          <TermsSection
            title="9) Termination"
            items={[
              'You may stop using the service at any time.',
              'We may suspend or terminate access if these Terms are violated or when required to protect service integrity or legal compliance.',
            ]}
          />

          <TermsSection
            title="10) Changes to terms"
            items={[
              'We may update these Terms from time to time.',
              'If changes are material, we will provide notice through the app, email, or other reasonable means.',
              'Continued use after updates become effective constitutes acceptance of the revised Terms.',
            ]}
          />

          <div className="rounded-xl border border-[#c6c6cd] bg-[#f7f9fb] p-5">
            <h2 className="text-lg font-semibold text-[#000000]">Contact</h2>
            <p className="mt-2 text-[15px] leading-[1.55] text-[#45464d]">
              Questions about these Terms can be sent to{' '}
              <a className="font-semibold text-[#006a61] underline-offset-4 hover:underline" href="mailto:legal@doubow.com">
                legal@doubow.com
              </a>.
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}

function TermsSection({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[#000000]">{title}</h2>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-[15px] leading-[1.55] text-[#45464d]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
