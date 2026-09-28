"use client";

import { MetricCard, formatCurrency, formatPercent, formatRatioAsPercent } from "@/components/ui/metric";
import { SectionHeading } from "@/components/ui/page-header";

type Props = {
  intrinsicValue: number;
  currentPrice: number;
  upside: number;
  discountRate: number;
};

export function ValuationCards({
  intrinsicValue,
  currentPrice,
  upside,
  discountRate,
}: Props) {
  return (
    <section
      id="valuation"
      data-testid="valuation-cards"
      aria-labelledby="valuation-heading"
      className="space-y-5 scroll-mt-32"
    >
      <SectionHeading
        id="valuation-heading"
        title="Valuation"
        description="Backend DCF output for this ticker."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Intrinsic value"
            value={formatCurrency(intrinsicValue)}
            hint="Estimated fair value per share"
            emphasis="primary"
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
            hint={
              upside >= 0
                ? "Intrinsic value above price"
                : "Intrinsic value below price"
            }
          />

          <MetricCard
            label="Discount rate"
            value={formatRatioAsPercent(discountRate)}
            hint="WACC used by the backend DCF"
          />
      </div>

      <p className="text-caption text-subtle-foreground">
        Intrinsic value, upside and the discount rate are model outputs from the
        backend valuation endpoint, not live market data.
      </p>
    </section>
  );
}
