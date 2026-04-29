import { SignUp } from "@clerk/nextjs";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import type { Route } from "next";
import { clerkAppearance } from "@/lib/clerk-appearance";

function safeRedirectPath(value: string | string[] | undefined): string | null {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw) return null;
  if (!raw.startsWith("/") || raw.startsWith("//")) return null;
  return raw;
}

export default async function AuthSignUpPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const redirectTarget = safeRedirectPath(params.redirect_url);
  const { userId } = await auth();
  if (userId) redirect((redirectTarget || "/dashboard") as Route);

  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return (
      <div className="rounded-xl border border-[0.5px] border-slate-200 bg-white p-5 text-sm text-[#3d4947] shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
        <p className="font-semibold text-[#171d1c] dark:text-slate-100">Clerk sign-up is not configured</p>
        <p className="mt-2 leading-relaxed">
          Set{' '}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-[#171d1c] dark:bg-slate-800 dark:text-slate-200">
            NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
          </code>{' '}
          in{' '}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">apps/web/.env.local</code> or the
          repo root <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">.env</code>, then restart{' '}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">next dev</code>.
        </p>
      </div>
    )
  }

  return (
    <SignUp
      appearance={clerkAppearance}
      path="/auth/sign-up"
      routing="path"
      signInUrl="/auth/sign-in"
      fallbackRedirectUrl={redirectTarget || "/dashboard"}
    />
  );
}
