import Image from "next/image";

export function DashboardPreview() {
  return (
    <div className="relative mx-auto max-w-6xl px-4 pb-4 sm:px-6 lg:px-8">
      <div
        className="overflow-hidden rounded-3xl border border-zinc-800 bg-black"
        style={{
          boxShadow:
            "0 -24px 80px -32px rgba(74,222,128,0.2), inset 0 1px 0 0 rgba(74,222,128,0.12)",
        }}
      >
        <div className="relative min-h-[420px] md:min-h-[480px]">
          <Image
            src="/reference/landing/hero-dashboard-real.png"
            alt="Doubow dashboard preview"
            fill
            priority
            className="object-cover object-center"
            sizes="(max-width: 1024px) 100vw, 1152px"
          />
        </div>
      </div>
    </div>
  );
}
