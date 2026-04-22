"use client";

import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import type { Route } from "next";
import { useState } from "react";
import { Logo } from "@/components/Logo";

const nav = [
  { href: "#product", label: "Product" },
  { href: "#future-resumes", label: "Résumés" },
  { href: "#how", label: "How it works" },
  { href: "#testimonials", label: "Testimonials" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export function Header() {
  const [open, setOpen] = useState(false);
  const mobileNavId = "landing-mobile-nav";

  return (
    <header className="landing-header sticky top-0 z-50 border-b shadow-[0_1px_0_0_rgb(24_24_27_/_0.06)]">
      <div className="relative mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        <Logo href="/" />

        <nav
          className="absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 items-center gap-8 md:flex"
          aria-label="Primary"
        >
          {nav.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-zinc-600 transition hover:text-zinc-900"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <SignedOut>
            <Link
              href={"/auth/sign-in" as Route}
              prefetch
              className="hidden rounded-full border border-zinc-200 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 shadow-sm transition hover:border-zinc-300 hover:bg-zinc-50 sm:inline-flex sm:items-center sm:justify-center"
            >
              Log in
            </Link>
            <Link
              href={"/auth/sign-up" as Route}
              prefetch
              className="hidden rounded-full border border-indigo-600 bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm shadow-indigo-600/20 transition hover:bg-indigo-700 hover:border-indigo-700 sm:inline-flex sm:items-center sm:justify-center"
            >
              Get started
            </Link>
          </SignedOut>
          <SignedIn>
            <UserButton
              appearance={{
                elements: {
                  userButtonAvatarBox: "h-9 w-9 ring-2 ring-zinc-700",
                },
              }}
            />
          </SignedIn>
          <button
            type="button"
            className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 md:hidden"
            aria-expanded={open}
            aria-controls={mobileNavId}
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            Menu
          </button>
        </div>
      </div>

      {open ? (
        <div id={mobileNavId} className="border-t border-zinc-200 bg-white px-4 py-4 md:hidden">
          <div className="flex flex-col gap-3">
            {nav.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-sm text-zinc-700"
                onClick={() => setOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <div className="flex flex-col gap-2">
              <SignedOut>
                <Link
                  href={"/auth/sign-in" as Route}
                  prefetch
                  className="block rounded-full border border-zinc-200 bg-white py-2 text-center text-sm font-semibold text-zinc-700"
                  onClick={() => setOpen(false)}
                >
                  Log in
                </Link>
                <Link
                  href={"/auth/sign-up" as Route}
                  prefetch
                  className="block rounded-full border border-indigo-600 bg-indigo-600 py-2 text-center text-sm font-semibold text-white"
                  onClick={() => setOpen(false)}
                >
                  Get started
                </Link>
              </SignedOut>
              <SignedIn>
                <div className="flex justify-center py-2">
                  <UserButton />
                </div>
              </SignedIn>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}
