"use client";

import { Crown } from "lucide-react";

import { useCompare } from "@/hooks/use-compare";
import { ErrorDisplay } from "@/components/ui/error-display";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonTable } from "@/components/ui/skeleton";
import {
  formatCurrency,
  formatPercent,
  formatRatio,
} from "@/components/ui/metric";
import { RecommendationBadge, TickerBadge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import type { CompareItemData } from "@/types/analysis";

type Props = {
  tickers: string[];
};

type Row = {
  metric: string;
  cells: (string | null)[];
  align: "left" | "right";
};

function toRows(results: CompareItemData[]): Row[] {
  return [
    {
      metric: "Intrinsic value",
      align: "right",
      cells: results.map((company) => formatCurrency(company.intrinsic_value)),
    },
    {
      metric: "Upside",
      align: "right",
      cells: results.map((company) => formatPercent(company.upside)),
    },
    {
      metric: "Recommendation",
      align: "left",
      cells: results.map((company) => company.recommendation),
    },
    {
      metric: "Health score",
      align: "right",
      cells: results.map((company) =>
        company.health_score == null
          ? null
          : `${formatRatio(company.health_score)}/100`
      ),
    },
  ];
}

const MISSING = "—";

export function ComparisonTable({ tickers }: Props) {
  const { data, isLoading, error, refetch } = useCompare(tickers);

  if (tickers.length < 2) {
    return (
      <EmptyState
        compact
        title="Add at least two tickers to compare"
        description="Use the field above to build the comparison set."
      />
    );
  }

  if (isLoading) {
    return (
      <div role="status" aria-busy="true">
        <SkeletonTable rows={5} cols={tickers.length + 1} />
        <span className="sr-only">Loading comparison…</span>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error}
        onRetry={() => refetch()}
        title="Comparison Failed"
        compact
      />
    );
  }

  const result = data?.data?.results ?? [];
  const best = data?.data?.best;
  const rows = toRows(result);

  if (result.length === 0) {
    return (
      <EmptyState
        compact
        title="No comparison data returned"
        description="The backend returned no comparison data for the selected tickers."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {result.map((company) => {
          const isBest = best === company.ticker;

          return (
            <div
              key={company.ticker}
              className={cn(
                "rounded-xl border bg-card px-4 py-4 shadow-card",
                isBest ? "border-gain/40" : "border-border"
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <TickerBadge symbol={company.ticker} className="px-2 py-1 text-body" />

                {isBest && (
                  <span className="inline-flex items-center gap-1 text-caption font-medium text-gain">
                    <Crown size={12} aria-hidden="true" />
                    Best pick
                  </span>
                )}
              </div>

              <p className="mt-2 truncate text-caption text-muted-foreground">
                {company.name ?? "Company name unavailable"}
              </p>

              <p className="tnum mt-3 text-metric text-foreground">
                {formatCurrency(company.intrinsic_value)}
              </p>
              <p className="mt-0.5 text-caption text-subtle-foreground">
                Intrinsic value per share
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <RecommendationBadge recommendation={company.recommendation} />
                <span
                  className={cn(
                    "tnum text-caption font-medium",
                    company.upside >= 0 ? "text-gain" : "text-loss"
                  )}
                >
                  {formatPercent(company.upside)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-card">
        <div className="max-h-[70vh] overflow-auto">
          <table className="w-full border-collapse text-label">
            <caption className="sr-only">
              Backend comparison of intrinsic value, upside, recommendation and
              health score for{" "}
              {result.map((company) => company.ticker).join(", ")}. The column the
              backend scored highest is marked “best pick”.
            </caption>

            <thead className="sticky top-0 z-10 border-b border-border bg-surface/90 backdrop-blur-sm">
              <tr>
                <th
                  scope="col"
                  className="px-4 py-3 text-left text-caption font-semibold uppercase tracking-[0.07em] text-subtle-foreground"
                >
                  Metric
                </th>

                {result.map((company) => (
                  <th
                    key={company.ticker}
                    scope="col"
                    className={cn(
                      "px-4 py-3 text-center font-mono text-label font-semibold text-foreground",
                      best === company.ticker && "bg-gain-subtle"
                    )}
                  >
                    {company.ticker}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => (
                <tr key={row.metric} className="border-b border-border/70 last:border-0">
                  <th
                    scope="row"
                    className="px-4 py-3 text-left font-medium text-muted-foreground"
                  >
                    {row.metric}
                  </th>

                  {row.cells.map((cell, index) => (
                    <td
                      key={`${row.metric}-${result[index]?.ticker ?? index}`}
                      className={cn(
                        "tnum px-4 py-3",
                        best === result[index]?.ticker && "bg-gain-subtle",
                        row.align === "right" ? "text-right" : "text-left"
                      )}
                    >
                      {row.metric === "Recommendation" && cell ? (
                        <RecommendationBadge recommendation={cell} />
                      ) : (
                        <span
                          className={
                            cell === null
                              ? "text-muted-foreground"
                              : "text-foreground"
                          }
                        >
                          {cell ?? MISSING}
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
