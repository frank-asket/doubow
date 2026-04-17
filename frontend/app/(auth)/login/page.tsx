import { SignIn } from '@clerk/nextjs'

export default function LoginPage() {
  const hasClerk = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
      {hasClerk ? (
        <SignIn
          path="/login"
          routing="path"
          signUpUrl="/onboarding"
          forceRedirectUrl="/discover"
        />
      ) : (
        <div className="card p-6 max-w-md w-full">
          <h1 className="text-lg font-semibold text-surface-800">Clerk not configured</h1>
          <p className="text-sm text-surface-500 mt-2">
            Add `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` to your env to enable sign-in.
          </p>
        </div>
      )}
    </div>
  )
}
