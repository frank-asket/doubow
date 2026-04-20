import { SignUp } from "@clerk/nextjs";
import { clerkAppearance } from "@/lib/clerk-appearance";

export default function AuthSignUpPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return (
      <div className="rounded-xl border border-amber-500/35 bg-amber-500/10 p-5 text-sm text-amber-100">
        <p className="font-semibold text-amber-50">Clerk sign-up is not configured</p>
        <p className="mt-2 text-amber-100/90">
          Set <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> in{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">frontend/.env.local</code> or the repo root{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">.env</code>, then restart{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">next dev</code>.
        </p>
      </div>
    );
  }

  return (
    <SignUp
      appearance={clerkAppearance}
      path="/auth/sign-up"
      routing="path"
      signInUrl="/auth/sign-in"
      fallbackRedirectUrl="/dashboard"
      forceRedirectUrl="/dashboard"
    />
  );
}
