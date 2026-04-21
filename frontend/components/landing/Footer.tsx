import Link from "next/link";
import { Logo } from "@/components/Logo";
import { FooterLegalLinks } from "@/components/landing/FooterLegalLinks";
import { productName } from "@/lib/customer-config";

export function FooterCTA() {
  return (
    <section className="bg-white px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl rounded-2xl border border-neutral-300 bg-neutral-50 px-8 py-14 text-center sm:px-12 sm:py-16">
        <h2 className="text-3xl font-semibold tracking-tight text-neutral-1000 sm:text-4xl">
          Ready to organize your next career move?
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-lg text-neutral-700">
          Track roles, refine what you send employers, and practice interviews—without giving up control
          of where or how you apply.
        </p>
        <Link
          href="/discover"
          className="mt-8 inline-flex rounded-full bg-primary-500 px-9 py-3.5 text-sm font-semibold text-black shadow-[0_16px_40px_-18px_rgba(255,188,1,0.8)] transition hover:bg-primary-600"
        >
          Get started now
        </Link>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-neutral-300 bg-white pb-12 pt-10">
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
              <a href="/auth/sign-up" className="hover:text-neutral-900">
                Plans
              </a>
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
              <a href="/auth/sign-in" className="hover:text-neutral-900">
                Sign in
              </a>
            </li>
            <li>
              <a href="/auth/sign-up" className="hover:text-neutral-900">
                Create account
              </a>
            </li>
            <li>
              <Link href="/discover" className="hover:text-neutral-900">
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
