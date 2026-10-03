"use client";

import { useState } from "react";
import { LineChart } from "lucide-react";

import { useCompare } from "@/hooks/use-compare";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";

import { AIInsightsPanel } from "./ai-insights-panel";
import { ComparisonInput } from "./comparison-input";
import { ComparisonTable } from "./comparison-table";
import {
  CompanyComparisonCard,
  CompanyComparisonCardSkeleton,
} from "./company-comparison-card";
import {
  MetricTabPanel,
  MetricTabs,
  PanelPlaceholder,
  type MetricTabId,
} from "./metric-tabs";

const defaults = ["AAPL", "MSFT", "NVDA", "GOOGL"];

export function ComparisonWorkspace() {
  const [tickers, setTickers] = useState<string[]>(defaults);
  const [tab, setTab] = useState<MetricTabId>("key-metrics");

  function addTicker(ticker: string) {
    const symbol = ticker.trim().toUpperCase();

    if (
      !symbol ||
      !/^[A-Z]{1,5}$/.test(symbol) ||
      tickers.includes(symbol)
    ) {
      return;
    }

    setTickers((prev) => [...prev, symbol]);
  }

  function removeTicker(ticker: string) {
    setTickers((prev) => prev.filter((t) => t !== ticker));
  }

  const { data, isLoading, error, refetch } = useCompare(tickers);
  const results = data?.data?.results ?? [];
  const best = data?.data?.best;
  const hasEnoughTickers = tickers.length >= 2;

  // Rank is derived from the upside the backend already returned — sorted
  // descending, mirroring how the backend picks `best`. No new scoring is
  // introduced, the ordering only labels the existing numbers.
  const ranks = new Map<string, number>(
    [...results]
      .sort((a, b) => b.upside - a.upside)
      .map((company, index) => [company.ticker, index + 1])
  );

  return (
    <div className="space-y-6">
      <ComparisonInput
        tickers={tickers}
        onAdd={addTicker}
        onRemove={removeTicker}
        onClear={() => setTickers([])}
        isLoading={isLoading}
      />

      {hasEnoughTickers && error && !isLoading && (
        <ErrorDisplay
          error={error}
          onRetry={() => refetch()}
          title="Comparison Failed"
        />
      )}

      {hasEnoughTickers && !error && (
        <section aria-label="Selected company comparison cards">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {isLoading && results.length === 0
              ? tickers.slice(0, 8).map((ticker) => (
                  <CompanyComparisonCardSkeleton key={ticker} />
                ))
              : results.map((company) => (
                  <CompanyComparisonCard
                    key={company.ticker}
                    company={company}
                    isBest={best === company.ticker}
                    rank={ranks.get(company.ticker) ?? null}
                    onRemove={removeTicker}
                  />
                ))}
          </div>
        </section>
      )}

      {hasEnoughTickers && !error && (
        <>
          <MetricTabs active={tab} onChange={setTab} />

          <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,7fr)_minmax(0,3fr)]">
            <MetricTabPanel id={tab}>
              <ComparisonTable tickers={tickers} view={tab} />
            </MetricTabPanel>

            <AIInsightsPanel />
          </div>

          <section
            aria-labelledby="price-performance-heading"
            className="rounded-2xl border border-border bg-card p-4 shadow-card sm:p-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2
                id="price-performance-heading"
                className="flex items-center gap-2 text-[1.0625rem] font-semibold text-foreground"
              >
                <LineChart size={17} className="text-brand" aria-hidden="true" />
                Price performance
              </h2>
            </div>

            <PanelPlaceholder
              icon={LineChart}
              title="No price history in the comparison feed"
              description="The comparison endpoint returns point-in-time intrinsic value, upside, recommendation and health score. Historical series and time-range switching are not part of that response, so no chart is drawn here."
            />
          </section>
        </>
      )}

      {!hasEnoughTickers && (
        <EmptyState
          title="Add at least two tickers to compare"
          description="Use the field above to build the comparison set. Every value is computed by the backend /compare endpoint."
        />
      )}
    </div>
  );
}

