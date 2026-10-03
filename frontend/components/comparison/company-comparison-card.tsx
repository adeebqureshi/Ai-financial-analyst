"use client";

import { Crown, MoreHorizontal } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { CompanyLogo } from "@/components/company/company-logo";
import {
  EMPTY_VALUE,
  formatCurrency,
  formatPercent,
  formatRatio,
} from "@/components/ui/metric";
import { cn } from "@/lib/utils";

import type { CompareItemData } from "@/types/analysis";

type Props = {
  company: CompareItemData;
  isBest: boolean;
  /** 1-based position by the backend-computed upside, or null when unknown. */
  rank?: number | null;
  onRemove?: (ticker: string) => void;
};

/**
 * Single comparison card.
 *
 * Only renders fields the `/compare` response actually returns
 * (intrinsic value, upside, recommendation, health score). The market
 * sparkline and live price are intentionally absent rather than invented —
 * the backend comparison payload carries no price history.
 */
export function CompanyComparisonCard({
  company,
  isBest,
  rank,
  onRemove,
}: Props) {
  return (
    <article
      aria-label={`${company.name ?? company.ticker} (${company.ticker}) comparison summary`}
      className={cn(
        "group flex flex-col rounded-2xl border bg-card px-4 py-4 shadow-card transition-[border-color,box-shadow,transform] duration-150 hover:-translate-y-0.5 hover:shadow-soft",
        isBest ? "border-brand/50" : "border-border hover:border-border-strong"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          {/* Logo, not the old hand-rolled `ticker.slice(0, 2)` monogram: the
              shared component resolves the real brand mark and only falls back
              to a monogram when a logo is genuinely unavailable. Decorative,
              since the symbol and name sit right beside it. */}
          <CompanyLogo
            ticker={company.ticker}
            companyName={company.name}
            size="md"
            decorative
          />

          <div className="min-w-0">
            <p className="truncate text-body font-semibold text-foreground">
              {company.ticker}
            </p>
            <p className="truncate text-caption text-muted-foreground">
              {company.name ?? EMPTY_VALUE}
            </p>
          </div>
        </div>

        {isBest ? (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-gain/25 bg-gain-subtle px-2 py-0.5 text-caption font-medium text-gain">
            <Crown size={12} aria-hidden="true" />
            Best pick
          </span>
        ) : onRemove ? (
          <button
            type="button"
            onClick={() => onRemove(company.ticker)}
            aria-label={`Remove ${company.ticker} from the comparison`}
            className="shrink-0 rounded-md p-1 text-subtle-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring group-hover:opacity-100"
          >
            <MoreHorizontal size={16} aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className="mt-4 flex items-end justify-between gap-3">
        <p className="tnum text-[1.6rem] font-bold leading-none tracking-[-0.02em] text-foreground">
          {formatCurrency(company.intrinsic_value)}
        </p>

        <span
          className={cn(
            "tnum inline-flex shrink-0 items-center rounded-md px-1.5 py-0.5 text-caption font-semibold",
            company.upside >= 0
              ? "bg-gain-subtle text-gain"
              : "bg-loss-subtle text-loss"
          )}
        >
          {formatPercent(company.upside)}
        </span>
      </div>

      <p className="mt-1.5 text-caption text-subtle-foreground">
        Intrinsic value · AI fair value estimate
      </p>

      <dl className="mt-3.5 grid grid-cols-3 gap-2 border-t border-border pt-3.5">
        <div className="min-w-0">
          <dt className="truncate text-caption text-subtle-foreground">Health</dt>
          <dd className="tnum mt-1 truncate text-[0.8125rem] font-semibold text-foreground">
            {company.health_score == null
              ? EMPTY_VALUE
              : `${formatRatio(company.health_score, 0)}/100`}
          </dd>
        </div>

        <div className="min-w-0">
          <dt className="truncate text-caption text-subtle-foreground">Rec.</dt>
          <dd className="mt-1 truncate text-[0.8125rem] font-semibold text-foreground">
            {company.recommendation}
          </dd>
        </div>

        <div className="min-w-0">
          <dt className="truncate text-caption text-subtle-foreground">Rank</dt>
          <dd className="tnum mt-1 truncate text-[0.8125rem] font-semibold text-foreground">
            {rank == null ? EMPTY_VALUE : `#${rank}`}
          </dd>
        </div>
      </dl>
    </article>
  );
}

export function CompanyComparisonCardSkeleton() {
  return (
    <div
      role="status"
      aria-busy="true"
      className="rounded-2xl border border-border bg-card px-4 py-4 shadow-card"
    >
      <div className="flex items-center gap-2.5">
        <Skeleton className="size-9 rounded-[5px]" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3.5 w-16" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <Skeleton className="mt-4 h-7 w-28" />
      <div className="mt-4 grid grid-cols-3 gap-3 border-t border-border pt-3">
        <Skeleton className="h-8" />
        <Skeleton className="h-8" />
        <Skeleton className="h-8" />
      </div>
      <span className="sr-only">Loading comparison…</span>
    </div>
  );
}
