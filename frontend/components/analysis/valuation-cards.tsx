"use client";

import {
  MetricCard,
  formatCurrency,
  formatPercent,
  formatRatioAsPercent,
} from "@/components/ui/metric";

type Props = {
  intrinsicValue: number;
  currentPrice: number;
  upside: number;
  discountRate: number;
};

/**
 * Valuation tiles for a completed analysis.
 *
 * All four values are returned by the backend valuation model; the UI adds no
 * commentary of its own beyond naming the model that produced the discount
 * rate (a WACC discount rate computed server-side).
 */
export function ValuationCards({
  intrinsicValue,
  currentPrice,
  upside,
  discountRate,
}: Props) {
  return (
    <section data-testid="valuation-cards" aria-labelledby="valuation-heading">
      <div className="mb-4">
        <h2 id="valuation-heading" className="text-title text-foreground">
          Valuation
        </h2>
        <p className="mt-1 text-label text-muted-foreground">
          Backend DCF output for this ticker.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Intrinsic value"
          value={formatCurrency(intrinsicValue)}
          hint="Estimated fair value per share"
        />

        <MetricCard
          label="Current price"
          value={formatCurrency(currentPrice)}
          hint="Latest market price"
        />

        <MetricCard
          label="Upside"
          value={formatPercent(upside)}
          delta={upside}
          hint={upside >= 0 ? "Intrinsic value above price" : "Intrinsic value below price"}
        />

        <MetricCard
          label="Discount rate"
          value={formatRatioAsPercent(discountRate)}
          hint="WACC used by the backend DCF"
        />
      </div>

      <p className="mt-3 text-caption text-subtle-foreground">
        Intrinsic value, upside and the discount rate are model outputs from the
        backend valuation endpoint, not live market data.
      </p>
    </section>
  );
}
