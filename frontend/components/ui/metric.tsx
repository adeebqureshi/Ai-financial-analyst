"use client";

import * as React from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "./card";

/** Rendered for null/undefined/NaN values instead of "null" or "NaN". */
export const EMPTY_VALUE = "—";

function isMissing(value: number | null | undefined): boolean {
  return value === null || value === undefined || Number.isNaN(value);
}

/** `1234.5` → `"$1,234.50"`. */
export function formatCurrency(
  value: number | null | undefined,
  maximumFractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits,
    minimumFractionDigits: maximumFractionDigits,
  }).format(value as number);
}

/**
 * `1240000000` → `"$1.24B"`.
 *
 * Compact notation for statement figures, which the backend expresses in
 * millions of USD.
 */
export function formatCompactCurrency(value: number | null | undefined): string {
  if (isMissing(value)) return EMPTY_VALUE;

  const amount = value as number;
  const abs = Math.abs(amount);

  if (abs >= 1e12) return `$${(amount / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(amount / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(amount / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `$${(amount / 1e3).toFixed(1)}K`;

  return `$${amount.toLocaleString()}`;
}

/** Formats a value that is already a percentage (`12.345` → `"12.35%"`). */
export function formatPercent(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return `${(value as number).toFixed(fractionDigits)}%`;
}

/**
 * Formats a ratio as a percentage (`0.1234` → `"12.34%"`).
 *
 * The backend returns ratios (not percentages) for yields, margins and
 * discount rates, so this helper is explicit about the ×100 conversion.
 */
export function formatRatioAsPercent(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return `${((value as number) * 100).toFixed(fractionDigits)}%`;
}

/** `1234567` → `"1,234,567"`. */
export function formatNumber(value: number | null | undefined): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return (value as number).toLocaleString();
}

/** `8.1227` → `"8.12"`; used for scores, ratios and betas. */
export function formatRatio(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return (value as number).toFixed(fractionDigits);
}

type DeltaProps = {
  /** Signed change. Negative values render in the loss tone. */
  value: number | null | undefined;
  /** `percent` appends "%" (default); `absolute` renders the raw number. */
  unit?: "percent" | "absolute";
  className?: string;
  /** Shows a dash icon and neutral tone when the value is exactly zero. */
  showZeroIcon?: boolean;
};

/**
 * Signed change indicator.
 *
 * Colour is semantic (gain/loss tokens) and the value always carries a sign so
 * the meaning never depends on colour alone.
 */
export function Delta({
  value,
  unit = "percent",
  className,
  showZeroIcon = true,
}: DeltaProps) {
  if (isMissing(value)) {
    return <span className={cn("text-muted-foreground", className)}>{EMPTY_VALUE}</span>;
  }

  const amount = value as number;
  const isZero = amount === 0;
  const positive = amount > 0;
  const Icon = isZero ? Minus : positive ? ArrowUpRight : ArrowDownRight;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 tnum text-label font-medium",
        isZero ? "text-muted-foreground" : positive ? "text-gain" : "text-loss",
        className
      )}
    >
      {(!isZero || showZeroIcon) && (
        <Icon className="size-3.5 shrink-0" aria-hidden="true" />
      )}
      {positive ? "+" : ""}
      {unit === "percent" ? `${amount.toFixed(2)}%` : amount.toFixed(2)}
    </span>
  );
}

type MetricCardProps = {
  label: string;
  value: React.ReactNode;
  /** Sub-label beneath the value (e.g. "Latest close"). */
  hint?: React.ReactNode;
  /** Optional signed change rendered next to the value. */
  delta?: number | null;
  deltaUnit?: "percent" | "absolute";
  icon?: React.ReactNode;
  className?: string;
  testId?: string;
};

/**
 * The single metric tile used across the workspace.
 *
 * Replaces the five near-identical card implementations that previously lived
 * in the dashboard, valuation, risk, health and market-overview components.
 */
export function MetricCard({
  label,
  value,
  hint,
  delta,
  deltaUnit = "percent",
  icon,
  className,
  testId,
}: MetricCardProps) {
  return (
    <Card data-testid={testId} className={cn("px-5 py-4", className)}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-label text-muted-foreground">{label}</p>
        {icon && <div className="shrink-0 text-muted-foreground">{icon}</div>}
      </div>

      <div className="mt-2 flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className="tnum text-display text-foreground">{value}</span>
        {delta !== undefined && <Delta value={delta} unit={deltaUnit} />}
      </div>

      {hint && <p className="mt-1 text-caption text-subtle-foreground">{hint}</p>}
    </Card>
  );
}