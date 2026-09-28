"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function ChartFrame({
  title,
  description,
  legend,
  children,
  className,
  footer,
}: {
  title: ReactNode;
  description?: ReactNode;
  legend?: ReactNode;
  children: ReactNode;
  className?: string;
  footer?: ReactNode;
}) {
  return (
    <figure
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-card shadow-card",
        className
      )}
    >
      <figcaption className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 border-b border-border px-5 py-3.5">
        <div className="min-w-0">
          <p className="text-label font-semibold text-foreground">{title}</p>
          {description && (
            <p className="mt-0.5 text-caption text-muted-foreground">
              {description}
            </p>
          )}
        </div>

        {legend && (
          <div className="flex flex-wrap items-center gap-3 text-caption text-muted-foreground">
            {legend}
          </div>
        )}
      </figcaption>

      <div className="px-5 py-5">{children}</div>

      {footer && (
        <div className="border-t border-border bg-surface/60 px-5 py-2.5 text-caption text-muted-foreground">
          {footer}
        </div>
      )}
    </figure>
  );
}

export function LegendDot({
  color,
  label,
}: {
  color: string;
  label: ReactNode;
}) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="size-2 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}

/**
 * Compares two values on a shared 0..max scale. Values come straight from the
 * backend payload — nothing is derived beyond the scale.
 */
export function ComparisonBars({
  rows,
  formatValue,
  className,
}: {
  rows: { label: string; value: number; tone?: "brand" | "gain" | "loss" }[];
  formatValue: (value: number) => string;
  className?: string;
}) {
  const max = Math.max(...rows.map((row) => Math.abs(row.value)), 1);
  const hasNegative = rows.some((row) => row.value < 0);

  return (
    <div className={cn("space-y-4", className)}>
      {rows.map((row) => {
        const ratio = Math.min(Math.abs(row.value) / max, 1);
        const tone =
          row.tone === "gain"
            ? "bg-gain"
            : row.tone === "loss"
              ? "bg-loss"
              : "bg-chart-1";

        return (
          <div key={row.label} className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-3">
              <span className="truncate text-label text-muted-foreground">
                {row.label}
              </span>
              <span className="tnum shrink-0 text-label font-medium text-foreground">
                {formatValue(row.value)}
              </span>
            </div>

            <div
              className="h-2 w-full overflow-hidden rounded-full bg-muted"
              role="img"
              aria-label={`${row.label}: ${formatValue(row.value)}`}
            >
              <div
                className={cn("h-full rounded-full transition-[width] duration-500", tone)}
                style={{ width: `${Math.max(ratio * 100, 1.5)}%` }}
              />
            </div>
          </div>
        );
      })}

      {hasNegative && (
        <p className="text-caption text-subtle-foreground">
          Bar length shows absolute magnitude.
        </p>
      )}
    </div>
  );
}

export function ScoreGauge({
  value,
  max = 100,
  label,
  caption,
  tone = "brand",
}: {
  value: number;
  max?: number;
  label: ReactNode;
  caption?: ReactNode;
  tone?: "brand" | "gain" | "warning" | "loss";
}) {
  const ratio = Math.max(0, Math.min(value / max, 1));
  const fill =
    tone === "gain"
      ? "bg-gain"
      : tone === "warning"
        ? "bg-warning"
        : tone === "loss"
          ? "bg-loss"
          : "bg-brand";

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-caption font-medium uppercase tracking-[0.08em] text-subtle-foreground">
          {label}
        </span>
        <span className="tnum text-subtitle text-foreground">{value}</span>
      </div>

      <div
        className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`${typeof label === "string" ? label : "Score"}: ${value} of ${max}`}
      >
        <div
          className={cn("h-full rounded-full transition-[width] duration-500", fill)}
          style={{ width: `${Math.max(ratio * 100, 1.5)}%` }}
        />
      </div>

      {caption && (
        <p className="text-caption text-muted-foreground">{caption}</p>
      )}
    </div>
  );
}

/**
 * Positions the current price inside the reported 52-week range.
 * Renders an unavailable state when the provider did not return a range.
 */
export function RangePosition({
  low,
  high,
  current,
  formatValue,
  label = "52-week range",
}: {
  low: number | null | undefined;
  high: number | null | undefined;
  current: number | null | undefined;
  formatValue: (value: number) => string;
  label?: string;
}) {
  const available =
    typeof low === "number" &&
    typeof high === "number" &&
    !Number.isNaN(low) &&
    !Number.isNaN(high) &&
    high > 0;

  if (!available) {
    return (
      <div className="space-y-2">
        <p className="text-caption font-medium uppercase tracking-[0.08em] text-subtle-foreground">
          {label}
        </p>
        <p className="text-label text-muted-foreground">
          Not provided by the market data provider.
        </p>
      </div>
    );
  }

  const span = (high as number) - (low as number);
  const ratio =
    typeof current === "number" && !Number.isNaN(current) && span > 0
      ? Math.max(0, Math.min(((current - (low as number)) / span) * 100, 100))
      : null;

  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-caption font-medium uppercase tracking-[0.08em] text-subtle-foreground">
          {label}
        </span>
        {ratio === null ? (
          <span className="text-caption text-muted-foreground">
            No current quote
          </span>
        ) : (
          <span className="tnum text-caption text-muted-foreground">
            {Math.round(ratio)}% of range
          </span>
        )}
      </div>

      <div className="relative h-8">
        <div className="absolute inset-x-0 top-1/2 h-2 -translate-y-1/2 rounded-full bg-muted" />
        <div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-chart-1/35"
          style={{
            left: 0,
            right: 0,
          }}
        />

        {ratio !== null && (
          <div
            className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-card bg-primary shadow-soft"
            style={{ left: `${ratio}%` }}
            aria-hidden="true"
          />
        )}
      </div>

      <div className="flex items-baseline justify-between gap-3 text-caption">
        <span className="tnum text-muted-foreground">
          Low {formatValue(low as number)}
        </span>
        <span className="tnum text-muted-foreground">
          High {formatValue(high as number)}
        </span>
      </div>
    </div>
  );
}

/**
 * Intrinsic value versus market price on a shared per-share scale.
 */
export function ValuationBridge({
  price,
  intrinsic,
  formatValue,
}: {
  price: number | null | undefined;
  intrinsic: number | null | undefined;
  formatValue: (value: number) => string;
}) {
  const hasBoth =
    typeof price === "number" &&
    typeof intrinsic === "number" &&
    !Number.isNaN(price) &&
    !Number.isNaN(intrinsic);

  if (!hasBoth) {
    return (
      <p className="text-label text-muted-foreground">
        Both a current price and an intrinsic value are required to plot this
        comparison.
      </p>
    );
  }

  const max = Math.max(price as number, intrinsic as number, 0.01);
  const delta = (intrinsic as number) - (price as number);
  const positive = delta >= 0;

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-label text-muted-foreground">Current price</span>
          <span className="tnum text-label font-medium text-foreground">
            {formatValue(price as number)}
          </span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-chart-3 transition-[width] duration-500"
            style={{ width: `${Math.max(((price as number) / max) * 100, 2)}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-label text-muted-foreground">Intrinsic value</span>
          <span className="tnum text-label font-medium text-foreground">
            {formatValue(intrinsic as number)}
          </span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-500",
              positive ? "bg-chart-1" : "bg-loss"
            )}
            style={{ width: `${Math.max(((intrinsic as number) / max) * 100, 2)}%` }}
          />
        </div>
      </div>

      <p
        className={cn(
          "tnum border-t border-border pt-3 text-label",
          positive ? "text-gain" : "text-loss"
        )}
      >
        {positive ? "+" : ""}
        {formatValue(delta)} per share {positive ? "above" : "below"} the market
        price
      </p>
    </div>
  );
}
