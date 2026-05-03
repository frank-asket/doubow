import Link from 'next/link'
import type { Metadata } from 'next'
import type { Route } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | Doubow',
  description: 'How Doubow collects, uses, and protects personal information.',
}

const lastUpdated = 'April 29, 2026'

export default function PrivacyPolicyPage() {
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
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-primary-green">Legal</p>
          <h1 className="mt-3 font-display text-4xl font-semibold tracking-[-0.02em] text-[#000000]">Privacy Policy</h1>
          <p className="mt-4 text-[16px] leading-[1.6] text-[#45464d]">
            This policy explains what information Doubow collects, why we collect it, and the choices you have.
          </p>
          <p className="mt-4 text-sm text-[#45464d]">Last updated: {lastUpdated}</p>
        </header>

        <section className="mt-8 space-y-6 rounded-2xl border border-[#c6c6cd] bg-white p-8 shadow-sm">
          <PolicySection
            title="1) Information we collect"
            items={[
              'Account details, such as name, email address, and authentication identifiers.',
              'Profile and job-search information you provide, such as resume content, preferences, and target roles.',
              'Usage data, including feature interactions, session events, and basic device/browser metadata.',
              'Support communications you send to our team.',
            ]}
          />

          <PolicySection
            title="2) How we use information"
            items={[
              'Provide and improve the Doubow product experience.',
              'Generate tailored job-search content and recommendations you request.',
              'Maintain security, prevent abuse, and troubleshoot issues.',
              'Communicate product updates, billing notices, and important service messages.',
            ]}
          />

          <PolicySection
            title="3) Legal bases (where applicable)"
            items={[
              'Performance of a contract when delivering the service you signed up for.',
              'Legitimate interests, such as product security and reliability.',
              'Consent for optional communications or processing when required by law.',
              'Compliance with legal obligations.',
            ]}
          />

          <PolicySection
            title="4) Sharing of information"
            items={[
              'We do not sell personal information.',
              'We may share information with service providers that help us run Doubow (hosting, analytics, support, billing).',
              'We may disclose information when required by law or to protect rights, safety, and platform integrity.',
            ]}
          />

          <PolicySection
            title="5) Data retention"
            items={[
              'We retain data only as long as needed for the purposes described in this policy.',
              'Retention periods may vary based on account status, legal requirements, and operational needs.',
              'You may request deletion of your account and associated personal information, subject to legal exceptions.',
            ]}
          />

          <PolicySection
            title="6) Security"
            items={[
              'We use administrative, technical, and organizational safeguards designed to protect personal information.',
              'No system is 100% secure, but we continuously monitor and improve our controls.',
            ]}
          />

          <PolicySection
            title="7) Your rights and choices"
            items={[
              'Depending on your location, you may have rights to access, correct, delete, or export your personal data.',
              'You may also object to or limit certain processing in some jurisdictions.',
              'To exercise rights, contact us using the details below.',
            ]}
          />

          <PolicySection
            title="8) International data transfers"
            items={[
              'If information is transferred across borders, we use appropriate safeguards where required by law.',
            ]}
          />

          <PolicySection
            title="9) Children’s privacy"
            items={[
              'Doubow is not intended for children under 16, and we do not knowingly collect their personal information.',
            ]}
          />

          <PolicySection
            title="10) Changes to this policy"
            items={[
              'We may update this policy from time to time. Material changes will be communicated through the app or email when appropriate.',
            ]}
          />

          <div className="rounded-xl border border-[#c6c6cd] bg-[#f7f9fb] p-5">
            <h2 className="text-lg font-semibold text-[#000000]">Contact us</h2>
            <p className="mt-2 text-[15px] leading-[1.55] text-[#45464d]">
              Questions about this policy can be sent to{' '}
              <a className="font-semibold text-primary-green underline-offset-4 hover:underline" href="mailto:privacy@doubow.com">
                privacy@doubow.com
              </a>.
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}

function PolicySection({ title, items }: { title: string; items: string[] }) {
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
