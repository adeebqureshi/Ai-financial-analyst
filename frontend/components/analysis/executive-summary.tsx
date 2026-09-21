"use client";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MetricCard,
  formatCurrency,
  formatPercent,
} from "@/components/ui/metric";
import { RecommendationBadge } from "@/components/ui/badge";

type Props = {
  recommendation: string;
  /**
   * Company profile text from `/analyze`, or null when the backend has none.
   * The UI never invents a narrative when it is absent.
   */
  summary: string | null;
  upside: number;
  intrinsicValue: number;
  currentPrice: number;
};

/**
 * Headline read of a completed analysis.
 *
 * Every figure here is a backend value: the recommendation, the intrinsic
 * value, the current price and the upside percentage. The only derived number
 * is the per-share difference between intrinsic value and price, which is
 * labelled as such.
 */
export function ExecutiveSummary({
  recommendation,
  summary,
  upside,
  intrinsicValue,
  currentPrice,
}: Props) {
  const difference = intrinsicValue - currentPrice;

  return (
    <section data-testid="executive-summary" aria-labelledby="analysis-summary-heading">
      <Card>
        <CardHeader>
          <div className="min-w-0">
            <CardTitle as="h2" id="analysis-summary-heading">
              Analysis summary
            </CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              Recommendation and valuation returned by the backend.
            </p>
          </div>

          <RecommendationBadge recommendation={recommendation} />
        </CardHeader>

        <CardBody className="space-y-6">
          {summary ? (
            <p className="max-w-4xl text-body text-muted-foreground">{summary}</p>
          ) : (
            <p className="text-body text-subtle-foreground">
              The backend did not return a company profile for this ticker.
            </p>
          )}

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Backend upside"
              value={formatPercent(upside)}
              delta={upside}
              hint="Intrinsic value vs. current price"
            />

            <MetricCard
              label="Intrinsic value"
              value={formatCurrency(intrinsicValue)}
              hint="Backend valuation model"
            />

            <MetricCard
              label="Current price"
              value={formatCurrency(currentPrice)}
              hint="Latest market quote"
            />

            <MetricCard
              label="Intrinsic − price"
              value={formatCurrency(difference)}
              hint="Per-share difference"
            />
          </div>
        </CardBody>
      </Card>
    </section>
  );
}