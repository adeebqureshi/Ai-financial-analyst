"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import {
  getCompanyLogoUrl,
  getCompanyName,
  getMonogram,
  normalizeTicker,
} from "@/lib/company-logos";

/**
 * Container scale. Fixed pixel sizes rather than Tailwind's `size-*` utilities
 * so the number passed to the logo provider always matches the rendered box —
 * a 20px chip must not request a 128px asset.
 */
const SIZES = {
  xs: 20,
  sm: 28,
  md: 36,
  lg: 52,
} as const;

export type CompanyLogoSize = keyof typeof SIZES;

export type CompanyLogoProps = {
  ticker: string | null | undefined;
  size?: CompanyLogoSize;
  /**
   * Overrides the registry name. The backend's `company.name` is authoritative
   * ("Apple Inc."), so callers holding a real profile should pass it through.
   */
  companyName?: string | null;
  /**
   * Hide from assistive tech. Correct whenever the company name is rendered
   * immediately beside the logo, since the logo would then be a duplicate
   * announcement.
   */
  decorative?: boolean;
  className?: string;
};

/**
 * The one company-identity primitive for the whole app.
 *
 * Renders a brand mark inside a neutral, near-white rounded container. The
 * surface is deliberately brand-neutral (`--card`, not `--brand`) so original
 * company colours are not tinted or filtered — a filter or brand-tinted plate
 * would misrepresent the logo, and a fixed white plate would disappear in dark
 * mode.
 *
 * Three layers of degradation, in order: remote image → monogram → nothing.
 * `onError` swaps in the monogram, so a blocked request, an offline client or
 * a dead provider degrades to a clean initial instead of a broken-image icon.
 */
export function CompanyLogo({
  ticker,
  size = "sm",
  companyName,
  decorative = false,
  className,
}: CompanyLogoProps) {
  // Track which URL failed rather than a bare boolean, so a ticker change can be
  // detected during render (see below) instead of via an effect.
  const [failedUrl, setFailedUrl] = React.useState<string | null>(null);

  const symbol = normalizeTicker(ticker);
  const pixels = SIZES[size];
  const url = getCompanyLogoUrl(symbol, pixels * 2);
  const name = getCompanyName(symbol, companyName);
  const monogram = getMonogram(symbol);

  // A ticker change must clear the previous symbol's failure, otherwise AAPL
  // failing would make every later ticker render as a monogram too. Adjusting
  // state during render is React's documented pattern for derived-from-props
  // state, and avoids an effect that would repaint the old logo first.
  const [lastSymbol, setLastSymbol] = React.useState(symbol);

  if (symbol !== lastSymbol) {
    setLastSymbol(symbol);
    setFailedUrl(null);
  }

  // Unknown ticker: render nothing rather than an empty bordered box, so
  // call sites can use this unconditionally without guarding.
  if (!symbol) return null;

  const showImage = Boolean(url) && failedUrl !== url;

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden",
        "rounded-[5px] border border-border bg-card shadow-[0_1px_2px_rgba(44,30,23,0.05)]",
        "dark:border-border dark:bg-card dark:shadow-none",
        className
      )}
      style={{ width: pixels, height: pixels }}
      {...(decorative
        ? { "aria-hidden": true as const }
        : { role: "img", "aria-label": `${name} logo` })}
    >
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url as string}
          alt=""
          width={pixels}
          height={pixels}
          loading="lazy"
          decoding="async"
          onError={() => setFailedUrl(url)}
          className="size-full object-contain"
        />
      ) : (
        <span
          aria-hidden="true"
          className={cn(
            "tnum flex size-full items-center justify-center font-semibold leading-none text-muted-foreground",
            size === "xs" ? "text-[9px]" : size === "lg" ? "text-[13px]" : "text-[11px]"
          )}
        >
          {monogram}
        </span>
      )}
    </span>
  );
}

/**
 * Logo + ticker + optional company name, as one identity block.
 *
 * Wraps rather than truncating so a narrow card drops the name to its own line
 * instead of clipping it, which keeps text legible down to 320px without
 * causing horizontal overflow.
 */
export function CompanyIdentity({
  ticker,
  companyName,
  size = "sm",
  showName = true,
  className,
}: {
  ticker: string | null | undefined;
  companyName?: string | null;
  size?: CompanyLogoSize;
  showName?: boolean;
  className?: string;
}) {
  const symbol = normalizeTicker(ticker);
  const name = getCompanyName(symbol, companyName);

  return (
    <span className={cn("flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5", className)}>
      <CompanyLogo
        ticker={symbol}
        companyName={companyName}
        size={size}
        decorative
      />

      <span className="flex min-w-0 flex-col">
        <span className="tnum truncate font-mono text-caption font-semibold tracking-[0.06em] text-foreground">
          {symbol}
        </span>

        {showName && name && name !== symbol ? (
          <span className="truncate text-caption text-muted-foreground">{name}</span>
        ) : null}
      </span>
    </span>
  );
}