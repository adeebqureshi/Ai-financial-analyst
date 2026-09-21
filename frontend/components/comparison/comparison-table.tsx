"use client";

import { useCompare } from "@/hooks/use-compare";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonTable } from "@/components/ui/skeleton";
import { formatCurrency, formatPercent, formatRatio } from "@/components/ui/metric";
import { RecommendationBadge } from "@/components/ui/badge";

import type { CompareItemData } from "@/types/analysis";

type Props = {
  tickers: string[];
};

type Row = {
  metric: string;
  /** `null` renders the explicit "not available" dash. */
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
      <div
        role="status"
        className="rounded-lg border border-dashed border-border px-6 py-10 text-center text-body text-muted-foreground"
      >
        Add at least two tickers to compare.
      </div>
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
      <div
        role="status"
        className="rounded-lg border border-dashed border-border px-6 py-10 text-center text-body text-muted-foreground"
      >
        The backend returned no comparison data for the selected tickers.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
      {/* Controlled horizontal scroll: the table grows with the number of
          tickers, the page itself never overflows. */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-label">
          <caption className="sr-only">
            Backend comparison of intrinsic value, upside, recommendation and
            health score for {result.map((company) => company.ticker).join(", ")}
            . The column the backend scored highest is marked “best pick”.
          </caption>

          <thead>
            <tr className="border-b border-border bg-muted/60">
              <th scope="col" className="px-4 py-3 text-left font-medium text-muted-foreground">
                Metric
              </th>

              {result.map((company) => (
                <th
                  key={company.ticker}
                  scope="col"
                  className={`px-4 py-3 text-center font-mono font-medium text-foreground ${
                    best === company.ticker ? "bg-gain-subtle" : ""
                  }`}
                >
                  {company.ticker}

                  {best === company.ticker && (
                    <span className="mt-0.5 block text-caption font-medium text-gain">
                      Best pick
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row) => (
              <tr
                key={row.metric}
                className="border-b border-border last:border-0"
              >
                <th
                  scope="row"
                  className="px-4 py-3 text-left font-medium text-muted-foreground"
                >
                  {row.metric}
                </th>

                {row.cells.map((cell, index) => (
                  <td
                    key={`${row.metric}-${result[index]?.ticker ?? index}`}
                    className={`tnum px-4 py-3 ${
                      best === result[index]?.ticker ? "bg-gain-subtle" : ""
                    } ${row.align === "right" ? "text-right" : "text-left"}`}
                  >
                    {row.metric === "Recommendation" && cell ? (
                      <RecommendationBadge recommendation={cell} />
                    ) : (
                      <span className={cell === null ? "text-muted-foreground" : "text-foreground"}>
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
