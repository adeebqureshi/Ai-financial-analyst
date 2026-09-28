"use client";

import * as React from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "./card";

export const EMPTY_VALUE = "—";

function isMissing(value: number | null | undefined): boolean {
  return value === null || value === undefined || Number.isNaN(value);
}

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

export function formatPercent(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return `${(value as number).toFixed(fractionDigits)}%`;
}

export function formatRatioAsPercent(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return `${((value as number) * 100).toFixed(fractionDigits)}%`;
}

export function formatNumber(value: number | null | undefined): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return (value as number).toLocaleString();
}

export function formatRatio(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (isMissing(value)) return EMPTY_VALUE;

  return (value as number).toFixed(fractionDigits);
}

type DeltaProps = {
  value: number | null | undefined;
  unit?: "percent" | "absolute";
  className?: string;
  showZeroIcon?: boolean;
};

export function Delta({
  value,
  unit = "percent",
  className,
  showZeroIcon = true,
}: DeltaProps) {
  if (isMissing(value)) {
    return (
      <span className={cn("text-muted-foreground", className)}>{EMPTY_VALUE}</span>
    );
  }

  const amount = value as number;
  const isZero = amount === 0;
  const positive = amount > 0;
  const Icon = isZero ? Minus : positive ? ArrowUpRight : ArrowDownRight;

  return (
    <span
      className={cn(
        "tnum inline-flex items-center gap-1 text-caption font-medium",
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

type MetricProps = {
  label: React.ReactNode;
  value: React.ReactNode;
  hint?: React.ReactNode;
  delta?: number | null;
  deltaUnit?: "percent" | "absolute";
  icon?: React.ReactNode;
  emphasis?: "default" | "primary";
  className?: string;
};

export function MetricCard({
  label,
  value,
  hint,
  delta,
  deltaUnit = "percent",
  icon,
  emphasis = "default",
  className,
  testId,
}: MetricProps & { testId?: string }) {
  return (
    <Card
      data-testid={testId}
      className={cn(
        "flex flex-col justify-between gap-3 px-5 py-4",
        emphasis === "primary" && "border-brand/30 bg-brand-subtle/40",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-caption font-medium uppercase tracking-[0.08em] text-subtle-foreground">
          {label}
        </p>
        {icon && (
          <div className="shrink-0 text-muted-foreground" aria-hidden="true">
            {icon}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span
          className={cn(
            "tnum text-metric text-foreground",
            emphasis === "primary" && "text-brand"
          )}
        >
          {value}
        </span>
        {delta !== undefined && <Delta value={delta} unit={deltaUnit} />}
      </div>

      {hint && <p className="text-caption text-muted-foreground">{hint}</p>}
    </Card>
  );
}

export function StatBlock({
  label,
  value,
  hint,
  className,
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("min-w-0", className)}>
      <p className="text-caption font-medium uppercase tracking-[0.08em] text-subtle-foreground">
        {label}
      </p>
      <p className="tnum mt-1.5 text-subtitle text-foreground">{value}</p>
      {hint && <p className="mt-1 text-caption text-muted-foreground">{hint}</p>}
    </div>
  );
}

type DefinitionRowProps = {
  label: React.ReactNode;
  value: React.ReactNode;
  className?: string;
  dense?: boolean;
};

export function DefinitionRow({
  label,
  value,
  className,
  dense = false,
}: DefinitionRowProps) {
  return (
    <div
      className={cn(
        "flex items-baseline justify-between gap-6 border-b border-border last:border-0",
        dense ? "py-2" : "py-2.5",
        className
      )}
    >
      <dt className="text-label text-muted-foreground">{label}</dt>
      <dd className="tnum shrink-0 text-label font-medium text-foreground">
        {value}
      </dd>
    </div>
  );
}
