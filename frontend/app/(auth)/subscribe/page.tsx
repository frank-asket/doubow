import Link from 'next/link'

export default function SubscribePage() {
  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
      <div className="card p-6 max-w-md w-full">
        <h1 className="text-lg font-semibold text-surface-800">Subscription required</h1>
        <p className="text-sm text-surface-500 mt-2">
          Your account is authenticated, but an active subscription is required to access the dashboard.
        </p>
        <p className="text-xs text-surface-400 mt-3">
          Set `public_metadata.subscriptionStatus = &quot;active&quot;` (or `public_metadata.plan`) in Clerk to unlock access.
        </p>
        <div className="mt-5 flex gap-2">
          <Link href="/onboarding" className="btn">
            Complete onboarding
          </Link>
          <Link href="/login" className="btn btn-primary">
            Switch account
          </Link>
        </div>
      </div>
    </div>
  )
}
