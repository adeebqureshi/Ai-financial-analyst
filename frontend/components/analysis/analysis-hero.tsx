"use client";

import {
  ChartCandlestick,
  Coins,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { cn } from "@/lib/utils";

const CAPABILITIES = [
  { label: "Financial data", icon: ChartCandlestick },
  { label: "Valuation models", icon: Coins },
  { label: "Risk analysis", icon: ShieldCheck },
  { label: "AI insights", icon: Sparkles },
];

/**
 * Decorative market artwork for the analysis hero.
 *
 * Purely presentational (`aria-hidden`), built from translucent surfaces and a
 * hand-drawn sparkline so the hero reads as financial without shipping a stock
 * photo or an extra image request. It is decorative only — every real value it
 * hints at is rendered by the live analysis workspace.
 */
function HeroArtwork({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute top-0 right-0 hidden h-full w-[38rem] select-none overflow-hidden lg:block",
        className
      )}
    >
      {/* Soft warm wash behind the artwork. */}
      <div className="absolute inset-y-0 right-0 w-full bg-[radial-gradient(120%_90%_at_75%_10%,color-mix(in_oklab,var(--brand)_22%,transparent),transparent_62%)]" />

      {/* Faded backdrop card. */}
      <div className="absolute top-16 right-40 h-40 w-72 -rotate-6 rounded-2xl border border-border/70 bg-card/45 opacity-70" />

      {/* Primary quote card. */}
      <div className="absolute top-8 right-6 w-72 rounded-2xl border border-border bg-card/85 p-4 shadow-overlay backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-lg bg-brand-subtle text-brand">
            <TrendingUp size={16} />
          </span>

          <div className="min-w-0">
            <p className="text-label font-semibold text-foreground">AAPL</p>
            <p className="truncate text-caption text-subtle-foreground">
              Apple Inc.
            </p>
          </div>

          <div className="ml-auto text-right">
            <p className="tnum text-label font-semibold text-foreground">
              175.43
            </p>
            <p className="tnum text-caption text-gain">+1.26%</p>
          </div>
        </div>

        {/* Candlestick-style sparkline. */}
        <svg
          viewBox="0 0 240 72"
          preserveAspectRatio="none"
          className="mt-4 h-16 w-full text-brand/85"
          role="presentation"
        >
          <polyline
            points="0,58 26,50 52,54 78,40 104,44 130,28 156,33 182,20 208,24 240,10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <polyline
            points="0,58 26,50 52,54 78,40 104,44 130,28 156,33 182,20 208,24 240,10 240,72 0,72"
            fill="color-mix(in oklab, var(--brand) 14%, transparent)"
            stroke="none"
          />
        </svg>
      </div>

      {/* Secondary translucent card, overlapping the primary one. */}
      <div className="absolute top-44 right-32 w-44 -rotate-3 rounded-xl border border-border bg-card/70 p-3 shadow-card backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="flex size-7 items-center justify-center rounded-md bg-info-subtle text-info">
            <ChartCandlestick size={13} />
          </span>
          <div className="min-w-0">
            <p className="text-caption font-semibold text-foreground">NVDA</p>
            <p className="truncate text-[10px] text-subtle-foreground">
              NVIDIA Corp.
            </p>
          </div>
        </div>

        <div className="mt-2.5 h-1.5 w-full rounded-full bg-muted" />
        <div className="mt-1.5 h-1.5 w-2/3 rounded-full bg-muted" />
      </div>

      {/* Ambient curve sweeping off the right edge. */}
      <svg
        viewBox="0 0 480 220"
        preserveAspectRatio="none"
        className="absolute top-28 right-0 h-52 w-[22rem] text-brand/45"
        role="presentation"
      >
        <path
          d="M0 200 C 80 200, 120 60, 200 60 S 320 150, 480 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>

      {/* Feather the artwork's left edge so it never cuts into the copy. */}
      <div className="absolute inset-y-0 left-0 w-40 bg-gradient-to-r from-background to-transparent" />
    </div>
  );
}

/**
 * Company analysis hero — page identity, the promise of the pipeline and the
 * capability set that backs it.
 *
 * The artwork is decorative and disappears below `lg`, where the header
 * naturally collapses to a single column and the illustration would compete
 * with the ticker form.
 */
export function AnalysisHero() {
  return (
    <header className="relative overflow-hidden">
      <HeroArtwork />

      <div className="relative min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-brand">
          Company &amp; Valuation
        </p>

        <h1 className="mt-2 text-display text-foreground">Company analysis</h1>

        <p className="mt-2 max-w-2xl text-body text-muted-foreground lg:max-w-[34rem]">
          Run the full AI pipeline for any public company — valuation, financial
          health, intrinsic value, risk analysis and a grounded AI copilot.
        </p>

        <ul className="mt-5 flex flex-wrap items-center gap-x-8 gap-y-3">
          {CAPABILITIES.map(({ label, icon: Icon }) => (
            <li
              key={label}
              className="flex items-center gap-2 text-label font-medium text-foreground"
            >
              <Icon size={16} className="text-brand" aria-hidden="true" />
              {label}
            </li>
          ))}
        </ul>
      </div>
    </header>
  );
}