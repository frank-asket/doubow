export function LogoMark({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect
        x="4"
        y="6"
        width="18"
        height="6"
        rx="1.5"
        fill="#FFBC01"
        transform="skewY(-14)"
      />
      <rect
        x="8"
        y="13"
        width="18"
        height="6"
        rx="1.5"
        fill="#FFBC01"
        opacity="0.78"
        transform="skewY(-14)"
      />
      <rect
        x="12"
        y="20"
        width="18"
        height="6"
        rx="1.5"
        fill="#FFBC01"
        opacity="0.52"
        transform="skewY(-14)"
      />
    </svg>
  );
}

export function Logo({ href = "/" }: { href?: string }) {
  const inner = (
    <span className="inline-flex items-center gap-2 font-bold tracking-tight text-neutral-1000">
      <LogoMark />
      Doubow
    </span>
  );

  if (href) {
    return (
      <a
        href={href}
        className="focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-100"
      >
        {inner}
      </a>
    );
  }

  return inner;
}
