import Link from "next/link";
import type { Route } from "next";
import { Logo } from "@/components/Logo";
import { FooterLegalLinks } from "@/components/landing/FooterLegalLinks";
import { productName } from "@/lib/customer-config";

export function FooterCTA() {
  return (
    <section className="border-t border-zinc-800/80 bg-gradient-to-b from-zinc-950 to-zinc-950 px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
      <div className="landing-panel mx-auto max-w-4xl rounded-2xl px-8 py-14 text-center sm:px-12 sm:py-16">
        <p className="landing-kicker">Career momentum</p>
        <h2 className="font-display mx-auto mt-5 max-w-2xl text-balance text-3xl font-semibold leading-tight tracking-tight text-zinc-100 sm:text-4xl">
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
    <footer className="border-t border-border-subtle bg-bg-light-green pb-12 pt-10">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        <div className="sm:col-span-2 lg:col-span-1">
          <Logo href="/" />
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-text-muted">
            Save jobs, shape application materials from your résumé, apply on official sites yourself,
            and use optional Gmail drafts you review before anything goes out.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold text-primary-green">Doubow</p>
          <ul className="mt-4 space-y-2 text-sm text-text-muted">
            <li>
              <a href="#why" className="hover:text-primary-green">
                Why Doubow?
              </a>
            </li>
            <li>
              <a href="#product" className="hover:text-primary-green">
                Product
              </a>
            </li>
            <li>
              <a href="#how" className="hover:text-primary-green">
                How it works
              </a>
            </li>
            <li>
              <Link href={"/auth/sign-up" as Route} prefetch className="hover:text-primary-green">
                Plans
              </Link>
            </li>
            <li>
              <a href="#faq" className="hover:text-primary-green">
                FAQ
              </a>
            </li>
            <li>
              <Link href="/discover" className="hover:text-primary-green">
                Open app
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-primary-green">Legal &amp; support</p>
          <ul className="mt-4 space-y-2 text-sm text-text-muted">
            <FooterLegalLinks />
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-primary-green">Product</p>
          <ul className="mt-4 space-y-2 text-sm text-text-muted">
            <li>
              <Link href={"/auth/sign-in" as Route} prefetch className="hover:text-primary-green">
                Sign in
              </Link>
            </li>
            <li>
              <Link href={"/auth/sign-up" as Route} prefetch className="hover:text-primary-green">
                Create account
              </Link>
            </li>
            <li>
              <Link href="/settings" className="hover:text-primary-green">
                Account settings
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <p className="mt-12 text-center text-xs text-text-muted">
        © {new Date().getFullYear()} {productName()}. All rights reserved.
      </p>
    </footer>
  );
}
