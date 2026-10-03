/**
 * Page hero for the comparison workspace.
 *
 * Decorative only: the market line, the soft glow and the neutral tiles are
 * drawn with inline SVG/CSS so the hero matches the reference composition
 * without shipping brand assets or adding a dependency. Everything inside the
 * artwork is `aria-hidden`, so the accessible name of the page is the
 * eyebrow/title/description only.
 */
export function ComparisonHero() {
  return (
    <header className="relative overflow-hidden px-1 pb-2 pt-1 sm:px-0">
      <div className="relative z-10 min-w-0 max-w-2xl">
        <p className="text-[13px] font-semibold uppercase tracking-[0.16em] text-brand">
          Markets &amp; Compare
        </p>

        <h1 className="mt-2.5 text-balance text-[2.5rem] font-bold leading-[1.05] tracking-[-0.03em] text-foreground sm:text-[2.75rem] lg:text-[3rem]">
          Company comparison
        </h1>

        <p className="mt-3.5 max-w-xl text-[0.9375rem] leading-relaxed text-muted-foreground sm:text-base">
          Compare multiple companies using AI valuation, financial health, risk
          analysis and intrinsic value.
        </p>
      </div>

      <div
        className="pointer-events-none absolute -bottom-6 right-0 top-0 hidden h-full w-[34rem] select-none lg:block xl:w-[40rem]"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 640 260"
          className="h-full w-full"
          preserveAspectRatio="xMidYMid meet"
          role="presentation"
        >
          <defs>
            <linearGradient id="compare-hero-wave" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--brand)" stopOpacity="0" />
              <stop offset="30%" stopColor="var(--brand)" stopOpacity="0.5" />
              <stop offset="70%" stopColor="var(--brand)" stopOpacity="0.95" />
              <stop offset="100%" stopColor="var(--brand)" stopOpacity="0.25" />
            </linearGradient>
            <linearGradient id="compare-hero-wave-soft" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--brand)" stopOpacity="0" />
              <stop offset="45%" stopColor="var(--brand)" stopOpacity="0.28" />
              <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
            </linearGradient>
            <radialGradient id="compare-hero-glow" cx="0.62" cy="0.35" r="0.55">
              <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.22" />
              <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="compare-hero-tile" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--card)" stopOpacity="0.98" />
              <stop offset="100%" stopColor="var(--surface)" stopOpacity="0.9" />
            </linearGradient>
          </defs>

          <rect x="0" y="0" width="640" height="260" fill="url(#compare-hero-glow)" />

          {/* rising market curve */}
          <path
            d="M40 214 C 120 206, 168 190, 214 182 S 300 168, 344 140 S 430 132, 470 108 S 560 96, 612 62"
            fill="none"
            stroke="url(#compare-hero-wave)"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="M40 236 C 130 230, 190 220, 244 214 S 350 202, 400 190 S 500 178, 612 166"
            fill="none"
            stroke="url(#compare-hero-wave-soft)"
            strokeWidth="1.75"
            strokeLinecap="round"
          />

          {[
            { cx: 344, cy: 140 },
            { cx: 470, cy: 108 },
            { cx: 612, cy: 62 },
          ].map((point) => (
            <circle
              key={`${point.cx}-${point.cy}`}
              cx={point.cx}
              cy={point.cy}
              r="3.5"
              fill="var(--card)"
              stroke="var(--brand)"
              strokeWidth="2"
            />
          ))}

          {/* neutral brand tiles riding the curve */}
          {[
            { x: 196, y: 118, size: 54, rotate: -8 },
            { x: 262, y: 96, size: 62, rotate: 5 },
            { x: 340, y: 66, size: 56, rotate: -4 },
            { x: 410, y: 44, size: 64, rotate: 7 },
          ].map((tile) => (
            <g
              key={tile.x}
              transform={`rotate(${tile.rotate} ${tile.x + tile.size / 2} ${tile.y + tile.size / 2})`}
            >
              <rect
                x={tile.x}
                y={tile.y}
                width={tile.size}
                height={tile.size}
                rx="16"
                fill="url(#compare-hero-tile)"
                stroke="var(--border)"
                strokeWidth="1"
              />
              <rect
                x={tile.x + tile.size * 0.3}
                y={tile.y + tile.size * 0.3}
                width={tile.size * 0.4}
                height={tile.size * 0.4}
                rx={tile.size * 0.11}
                fill="var(--brand)"
                fillOpacity="0.22"
              />
            </g>
          ))}
        </svg>
      </div>
    </header>
  );
}
