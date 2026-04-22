import Link from "next/link";
import type { Route } from "next";
import { Logo } from "@/components/Logo";
import { FooterLegalLinks } from "@/components/landing/FooterLegalLinks";
import { productName } from "@/lib/customer-config";

export function FooterCTA() {
  return (
    <section className="border-t border-zinc-200/80 bg-gradient-to-b from-zinc-50 to-white px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
      <div className="mx-auto max-w-4xl rounded-2xl border border-zinc-200 bg-white px-8 py-14 text-center shadow-md shadow-zinc-950/10 sm:px-12 sm:py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Career momentum</p>
        <h2 className="font-display mx-auto mt-5 max-w-2xl text-balance text-3xl font-semibold leading-tight tracking-tight text-zinc-950 sm:text-4xl">
          Ready to organize your next career move?
        </h2>
        <p className="landing-lede mx-auto mt-5 max-w-xl">
          Track roles, refine what you send employers, and practice interviews—without giving up control
          of where or how you apply.
        </p>
        <Link
          href="/discover"
          className="landing-btn-primary mt-10 px-9 py-3.5"
        >
          Get started now
        </Link>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-zinc-200/80 bg-zinc-50 pb-12 pt-10">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        <div className="sm:col-span-2 lg:col-span-1">
          <Logo href="/" />
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-neutral-500">
            Save jobs, shape application materials from your résumé, apply on official sites yourself,
            and use optional Gmail drafts you review before anything goes out.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-1000">Doubow</p>
          <ul className="mt-4 space-y-2 text-sm text-neutral-500">
            <li>
              <a href="#why" className="hover:text-neutral-900">
                Why Doubow?
              </a>
            </li>
            <li>
              <a href="#product" className="hover:text-neutral-900">
                Product
              </a>
            </li>
            <li>
              <a href="#how" className="hover:text-neutral-900">
                How it works
              </a>
            </li>
            <li>
              <Link href={"/auth/sign-up" as Route} prefetch className="hover:text-neutral-900">
                Plans
              </Link>
            </li>
            <li>
              <a href="#faq" className="hover:text-neutral-900">
                FAQ
              </a>
            </li>
            <li>
              <Link href="/discover" className="hover:text-neutral-900">
                Open app
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-1000">Legal &amp; support</p>
          <ul className="mt-4 space-y-2 text-sm text-neutral-500">
            <FooterLegalLinks />
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-1000">Product</p>
          <ul className="mt-4 space-y-2 text-sm text-neutral-500">
            <li>
              <Link href={"/auth/sign-in" as Route} prefetch className="hover:text-neutral-900">
                Sign in
              </Link>
            </li>
            <li>
              <Link href={"/auth/sign-up" as Route} prefetch className="hover:text-neutral-900">
                Create account
              </Link>
            </li>
            <li>
              <Link href="/settings" className="hover:text-neutral-900">
                Account settings
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <p className="mt-12 text-center text-xs text-neutral-600">
        © {new Date().getFullYear()} {productName()}. All rights reserved.
      </p>
    </footer>
  );
}
