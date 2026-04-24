import type { Metadata } from "next";
import { AuthBrandingPanel } from "@/components/auth/AuthBrandingPanel";

export const metadata: Metadata = {
  title: 'Account — Doubow',
  description:
    'Sign in or join Doubow—discover scored roles, run your pipeline with human-approved drafts, and prep for interviews in one Candidate Hub.',
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#f5faf8] text-[#171d1c] antialiased dark:bg-slate-950 dark:text-slate-100">
      <div className="flex min-h-screen flex-col lg:grid lg:grid-cols-[minmax(280px,420px)_1fr]">
        <AuthBrandingPanel />
        <main className="flex flex-1 items-center justify-center px-4 py-10 sm:px-8">
          <div className="w-full max-w-[420px]">{children}</div>
        </main>
      </div>
    </div>
  )
}
