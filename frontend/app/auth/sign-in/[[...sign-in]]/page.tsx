import { SignIn } from "@clerk/nextjs";
import { clerkAppearance } from "@/lib/clerk-appearance";

export default function AuthSignInPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return (
      <div className="rounded-xl border border-amber-500/35 bg-amber-500/10 p-5 text-sm text-amber-100">
        <p className="font-semibold text-amber-50">Clerk sign-in is not configured</p>
        <p className="mt-2 text-amber-100/90">
          Set <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> in{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">frontend/.env.local</code> or the repo root{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">.env</code> (see{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">frontend/.env.example</code>), then restart{" "}
          <code className="rounded bg-black/30 px-1.5 py-0.5 text-xs">next dev</code>.
        </p>
      </div>
    );
  }

  return (
    <SignIn
      appearance={clerkAppearance}
      path="/auth/sign-in"
      routing="path"
      signUpUrl="/auth/sign-up"
      fallbackRedirectUrl="/dashboard"
      forceRedirectUrl="/dashboard"
    />
  );
}
