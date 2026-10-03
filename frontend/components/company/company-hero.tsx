"use client";

import { Building2, Globe2 } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Decorative company-directory artwork.
 *
 * Purely presentational (`aria-hidden`) and CSS/SVG only: a globe, a building
 * and a chart tile assembled from the brand tokens, so the hero reads as
 * business without shipping an image request or a new dependency. It contains
 * no company names or figures — the real profile is always rendered by
 * `/company/[ticker]` from the backend.
 */
function HeroArtwork({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute top-0 right-0 hidden h-full w-[32rem] select-none overflow-hidden lg:block",
        className
      )}
    >
      {/* Warm wash behind the composition. */}
      <div className="absolute inset-0 bg-[radial-gradient(110%_120%_at_68%_50%,color-mix(in_oklab,var(--brand)_24%,transparent),transparent_66%)]" />

      {/* Everything below is vertically centred in the header band. The band is
          short (~6rem), so the tiles stay small — a large illustration would be
          clipped by the container rather than sit beside the copy. */}

      {/* Globe: wireframe rings over a warm disc. */}
      <div className="absolute top-1/2 right-44 size-24 -translate-y-1/2 rounded-full bg-brand-subtle/60 ring-1 ring-brand/15">
        <Globe2
          size={96}
          className="absolute inset-0 size-full text-brand/35"
          strokeWidth={0.75}
        />
      </div>

      {/* Building tile. */}
      <div className="absolute top-1/2 right-[19rem] -translate-y-1/2 -rotate-3 rounded-xl border border-border bg-card/85 p-2.5 shadow-overlay backdrop-blur-sm">
        <span className="flex size-7 items-center justify-center rounded-lg bg-brand-subtle text-brand">
          <Building2 size={15} />
        </span>
        <div className="mt-2 h-1.5 w-12 rounded-full bg-muted" />
        <div className="mt-1.5 h-1.5 w-7 rounded-full bg-muted" />
      </div>

      {/* Bar-chart tile, upper right. */}
      <div className="absolute top-1/2 right-6 -translate-y-1/2 rotate-2 rounded-lg border border-border bg-card/80 p-2.5 shadow-card backdrop-blur-sm">
        <svg
          viewBox="0 0 48 32"
          className="h-7 w-10 text-brand/70"
          role="presentation"
        >
          <rect x="4" y="16" width="7" height="14" rx="2" fill="currentColor" opacity="0.45" />
          <rect x="16" y="8" width="7" height="22" rx="2" fill="currentColor" opacity="0.7" />
          <rect x="28" y="2" width="7" height="28" rx="2" fill="currentColor" />
        </svg>
      </div>

      {/* Line-chart tile, lower right. */}
      <div className="absolute top-1/2 right-28 -translate-y-1/2 -rotate-2 rounded-lg border border-border bg-card/80 p-2.5 shadow-card backdrop-blur-sm">
        <svg
          viewBox="0 0 56 28"
          className="h-6 w-12 text-brand/70"
          role="presentation"
        >
          <polyline
            points="2,22 14,16 26,19 38,8 50,12 54,4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* Feather the left edge so the artwork never cuts into the copy. */}
      <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-background to-transparent" />
    </div>
  );
}

/**
 * Company directory hero — page identity and the promise of the lookup.
 *
 * The artwork is decorative and disappears below `lg`, where the header
 * collapses to a single column and the illustration would compete with the
 * ticker form.
 */
export function CompanyHero() {
  return (
    <header className="relative overflow-hidden">
      <HeroArtwork />

      <div className="relative min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-brand">
          Company &amp; Valuation
        </p>

        <h1 className="mt-2 text-display text-foreground">Companies</h1>

        <p className="mt-2 max-w-2xl text-body text-muted-foreground lg:max-w-[32rem]">
          Look up a public company, review its profile, and run the full AI
          analysis.
        </p>
      </div>
    </header>
  );
}