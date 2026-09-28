"use client";

import { Card, CardBody } from "@/components/ui/card";
import { Badge, RecommendationBadge } from "@/components/ui/badge";
import { formatCurrency, formatPercent } from "@/components/ui/metric";
import { SectionHeading } from "@/components/ui/page-header";
import { ChartFrame, ValuationBridge } from "./visuals";

type Props = {
  recommendation: string;

  summary: string | null;

  upside: number;

  intrinsicValue: number;

  currentPrice: number;

  healthScore?: number;
  healthRating?: string;
  piotroski?: number;
  riskLevel?: string | null;
};

type Driver = {
  label: string;
  value: string;
  tone?: "gain" | "loss" | "neutral";
  hint: string;
};

export function ExecutiveSummary({
  recommendation,
  summary,
  upside,
  intrinsicValue,
  currentPrice,
  healthScore,
  healthRating,
  piotroski,
  riskLevel,
}: Props) {
  const difference = intrinsicValue - currentPrice;
  const positive = difference >= 0;

  const drivers: Driver[] = [
    {
      label: "Valuation",
      value: `${formatPercent(upside)} vs. market`,
      tone: upside >= 0 ? "gain" : "loss",
      hint: `Intrinsic value ${formatCurrency(intrinsicValue)} against a price of ${formatCurrency(currentPrice)}.`,
    },
    {
      label: "Financial quality",
      value:
        typeof healthScore === "number"
          ? `${healthScore}/100${healthRating ? ` · ${healthRating}` : ""}`
          : "—",
      tone: "neutral",
      hint:
        typeof piotroski === "number"
          ? `Piotroski F-Score of ${piotroski}/9.`
          : "Backend health score returned by the analysis pipeline.",
    },
    {
      label: "Risk",
      value: riskLevel ?? "—",
      tone: "neutral",
      hint: "Composite risk level returned by the backend assessment.",
    },
    {
      label: "Recommendation",
      value: recommendation,
      tone: "neutral",
      hint: "Recommendation produced by the backend model — not investment advice.",
    },
  ];

  return (
    <section
      id="summary"
      data-testid="executive-summary"
      aria-labelledby="analysis-summary-heading"
      className="space-y-5 scroll-mt-32"
    >
      <SectionHeading
        id="analysis-summary-heading"
        title="Executive summary"
        description="The backend recommendation and DCF output for this ticker."
        actions={<RecommendationBadge recommendation={recommendation} />}
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
        <Card>
          <CardBody className="space-y-5">
            <ul className="divide-y divide-border">
              {drivers.map((driver) => (
                <li
                  key={driver.label}
                  className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-3 first:pt-0 last:pb-0"
                >
                  <span className="text-label text-muted-foreground">
                    {driver.label}
                  </span>

                  <span className="flex items-baseline gap-2">
                    {driver.tone === "gain" ? (
                      <Badge variant="success">{driver.value}</Badge>
                    ) : driver.tone === "loss" ? (
                      <Badge variant="danger">{driver.value}</Badge>
                    ) : (
                      <span className="tnum text-label font-semibold text-foreground">
                        {driver.value}
                      </span>
                    )}
                  </span>

                  <p className="w-full text-caption leading-relaxed text-muted-foreground">
                    {driver.hint}
                  </p>
                </li>
              ))}
            </ul>

            {summary ? (
              <p className="border-t border-border pt-4 text-caption leading-relaxed text-muted-foreground">
                {summary}
              </p>
            ) : (
              <p className="border-t border-border pt-4 text-caption text-subtle-foreground">
                The backend did not return a written narrative for this ticker.
              </p>
            )}

            <p
              className={
                positive
                  ? "tnum border-t border-border pt-4 text-label text-gain"
                  : "tnum border-t border-border pt-4 text-label text-loss"
              }
            >
              {positive ? "+" : ""}
              {formatCurrency(difference)} per share{" "}
              {positive ? "above" : "below"} the market price
            </p>
          </CardBody>
        </Card>

        <ChartFrame
          title="Valuation bridge"
          description="Per-share values returned by the backend"
          legend={<Badge variant="brand">DCF output</Badge>}
          footer="Model output from the valuation endpoint — not live market data."
        >
          <ValuationBridge
            price={currentPrice}
            intrinsic={intrinsicValue}
            formatValue={(value) => formatCurrency(value)}
          />
        </ChartFrame>
      </div>
    </section>
  );
}
