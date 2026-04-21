import { SignIn } from "@clerk/nextjs";
import { clerkAppearance } from "@/lib/clerk-appearance";

export default function AuthSignInPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return (
      <div className="rounded-xl border border-zinc-500/35 bg-zinc-800 p-5 text-sm text-zinc-200">
        <p className="font-semibold text-zinc-100">Clerk sign-in is not configured</p>
        <p className="mt-2 text-zinc-300">
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
