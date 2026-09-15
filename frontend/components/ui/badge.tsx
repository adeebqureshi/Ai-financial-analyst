import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const badgeVariants = cva(
  [
    "inline-flex items-center gap-1.5",
    "rounded-full border px-2.5 py-0.5",
    "text-caption font-medium",
    "whitespace-nowrap",
  ].join(" "),
  {
    variants: {
      variant: {
        neutral: "border-border bg-muted text-muted-foreground",
        outline: "border-border bg-transparent text-muted-foreground",
        brand: "border-brand/25 bg-brand-subtle text-brand",
        success: "border-gain/25 bg-gain-subtle text-gain",
        warning: "border-warning/25 bg-warning-subtle text-warning",
        danger: "border-loss/25 bg-loss-subtle text-loss",
        info: "border-info/25 bg-info-subtle text-info",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

type RecommendationTone = "success" | "warning" | "danger" | "neutral";

/**
 * Map a backend recommendation string to a semantic tone.
 *
 * Mirrors the previous `badgeColor()` behaviour: substring matching so values
 * like "STRONG BUY" keep working, with unknown values falling back to neutral.
 */
export function recommendationTone(recommendation: string): RecommendationTone {
  const normalized = recommendation.toUpperCase();

  if (normalized.includes("BUY")) return "success";
  if (normalized.includes("SELL")) return "danger";
  if (normalized.includes("HOLD")) return "warning";

  return "neutral";
}

export function RecommendationBadge({
  recommendation,
  className,
}: {
  recommendation: string;
  className?: string;
}) {
  return (
    <Badge variant={recommendationTone(recommendation)} className={className}>
      {recommendation}
    </Badge>
  );
}

const statusVariants: Record<string, VariantProps<typeof badgeVariants>["variant"]> = {
  done: "success",
  ok: "success",
  ready: "success",
  indexed: "success",
  healthy: "success",
  connected: "success",
  running: "info",
  checking: "info",
  pending: "warning",
  processing: "warning",
  degraded: "warning",
  skipped: "neutral",
  unknown: "neutral",
  error: "danger",
  failed: "danger",
  unavailable: "danger",
  unhealthy: "danger",
};

/** Status badge for backend health, agent tools and document states. */
export function StatusBadge({
  status,
  label,
  className,
}: {
  status: string;
  label?: string;
  className?: string;
}) {
  return (
    <Badge
      variant={statusVariants[status.toLowerCase()] ?? "neutral"}
      className={className}
    >
      {label ?? status}
    </Badge>
  );
}

/**
 * Marks data that is synthetic / not live market data.
 *
 * Used instead of inventing numbers: anything not backed by a real backend
 * response is labelled rather than presented as live.
 */
export function DemoBadge({
  label = "Demo data",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <Badge variant="warning" className={className}>
      {label}
    </Badge>
  );
}