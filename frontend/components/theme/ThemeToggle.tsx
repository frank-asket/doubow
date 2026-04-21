"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

export default function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="rounded-md border border-neutral-300/60 bg-neutral-50/40 px-3 py-1.5 text-xs font-medium text-neutral-900 transition-colors hover:bg-neutral-50/70 dark:border-neutral-300/30 dark:bg-neutral-50/10 dark:text-neutral-800 dark:hover:bg-neutral-50/20"
      aria-label="Toggle theme"
    >
      {isDark ? "Light mode" : "Dark mode"}
    </button>
  );
}
