"use client";

import { useAuth } from "@clerk/nextjs";

export default function DevAuthNotice() {
  const { isLoaded, isSignedIn } = useAuth();

  if (process.env.NODE_ENV !== "development") return null;
  if (!isLoaded || !isSignedIn) return null;

  return (
    <div className="pointer-events-none fixed bottom-3 right-3 z-[120] rounded-md border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-800 shadow-sm">
      Authenticated — auth routes redirected
    </div>
  );
}
