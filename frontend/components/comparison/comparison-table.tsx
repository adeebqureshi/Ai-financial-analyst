"use client";

import { useCompare } from "@/hooks/use-compare";
import { ErrorDisplay } from "@/components/ui/error-display";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonTable } from "@/components/ui/skeleton";
import {
  formatCurrency,
  formatPercent,
  formatRatio,
} from "@/components/ui/metric";
import { RecommendationBadge } from "@/components/ui/badge";
import { CompanyLogo } from "@/components/company/company-logo";
import { cn } from "@/lib/utils";

import type { CompareItemData } from "@/types/analysis";
import type { MetricTabId } from "./metric-tabs";

type Props = {
  tickers: string[];
  /** Restricts the rendered rows to the active metric tab. */
  view?: MetricTabId;
};

type Row = {
  metric: string;
  cells: (string | null)[];
  align: "left" | "right";
  badge?: boolean;
};

const ALL_ROWS: Record<MetricTabId, string[]> = {
  "key-metrics": [
    "Intrinsic value",
    "Upside",
    "Recommendation",
    "Health score",
  ],
  "financial-health": ["Health score", "Recommendation"],
  valuation: ["Intrinsic value", "Upside", "Recommendation"],
  "comparison-table": [
    "Intrinsic value",
    "Upside",
    "Recommendation",
    "Health score",
  ],
};

function buildRow(metric: string, results: CompareItemData[]): Row {
  switch (metric) {
    case "Intrinsic value":
      return {
        metric,
        align: "right",
        cells: results.map((company) => formatCurrency(company.intrinsic_value)),
      };
    case "Upside":
      return {
        metric,
        align: "right",
        cells: results.map((company) => formatPercent(company.upside)),
      };
    case "Recommendation":
      return {
        metric,
        align: "left",
        badge: true,
        cells: results.map((company) => company.recommendation),
      };
    case "Health score":
      return {
        metric,
        align: "right",
        cells: results.map((company) =>
          company.health_score == null
            ? null
            : `${formatRatio(company.health_score)}/100`
        ),
      };
    default:
      return { metric, align: "right", cells: results.map(() => null) };
  }
}

const MISSING = "—";

export function ComparisonTable({ tickers, view = "key-metrics" }: Props) {
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
  const rows = ALL_ROWS[view].map((metric) => buildRow(metric, result));

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
    <div className="min-w-0 overflow-x-auto">
      <div className="min-w-[36rem]">
        <table className="w-full border-collapse text-label">
            <caption className="sr-only">
              Backend comparison of intrinsic value, upside, recommendation and
              health score for{" "}
              {result.map((company) => company.ticker).join(", ")}. The column the
              backend scored highest is highlighted.
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
                    {/* Inline rather than stacked: a taller header would shift
                        every row, and the mark stays decorative because the
                        symbol is in the same cell. */}
                    <span className="inline-flex items-center gap-1.5">
                      <CompanyLogo ticker={company.ticker} size="xs" decorative />

                      {company.ticker}
                    </span>
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
                      {row.badge && cell ? (
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
  );
}
