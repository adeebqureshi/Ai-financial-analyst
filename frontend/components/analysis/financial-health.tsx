"use client";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { MetricCard, formatRatio } from "@/components/ui/metric";
import { SectionHeading } from "@/components/ui/page-header";
import { ChartFrame, ScoreGauge } from "./visuals";

type Props = {
  score: number;
  rating: string;
  piotroski: number;
  altman: number;
  beneish: number;
};

function bankruptcyRiskLabel(altman: number): string {
  if (altman > 3) return "Low";
  if (altman > 1.8) return "Moderate";
  return "High";
}

function manipulationRiskLabel(beneish: number): string {
  return beneish > -1.78 ? "High" : "Low";
}

function toneFor(level: string): BadgeProps["variant"] {
  if (level === "Low") return "success";
  if (level === "Moderate") return "warning";
  return "danger";
}

export function FinancialHealth({
  score,
  rating,
  piotroski,
  altman,
  beneish,
}: Props) {
  const bankruptcyRisk = bankruptcyRiskLabel(altman);
  const manipulationRisk = manipulationRiskLabel(beneish);

  const piotroskiRead =
    piotroski >= 7
      ? "strong financial quality"
      : piotroski >= 5
        ? "average financial quality"
        : "weak financial quality";

  return (
    <section
      id="health"
      data-testid="financial-health"
      aria-labelledby="health-heading"
      className="space-y-5 scroll-mt-32"
    >
      <SectionHeading
        id="health-heading"
        title="Financial health"
        description="Backend quality scores and their standard interpretation."
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div className="grid items-start gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Health score"
            value={`${score}/100`}
            hint={rating}
            emphasis="primary"
          />

          <MetricCard
            label="Piotroski F-Score"
            value={`${piotroski}/9`}
            hint="Financial strength"
          />

          <MetricCard
            label="Altman Z-Score"
            value={formatRatio(altman)}
            hint={`${bankruptcyRisk} bankruptcy risk`}
          />

          <MetricCard
            label="Beneish M-Score"
            value={formatRatio(beneish)}
            hint={`${manipulationRisk} manipulation risk`}
          />
        </div>

        <ChartFrame
          title="Score interpretation"
          description="Derived from the values on the left"
        >
          <div className="space-y-5">
            <ScoreGauge
              label="Health score"
              value={score}
              caption={`Backend rating: ${rating}`}
              tone={score >= 70 ? "gain" : score >= 50 ? "warning" : "loss"}
            />

            <dl className="space-y-2.5">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-label text-muted-foreground">
                  Bankruptcy risk (Altman Z)
                </dt>
                <dd>
                  <Badge variant={toneFor(bankruptcyRisk)}>
                    {bankruptcyRisk}
                  </Badge>
                </dd>
              </div>

              <div className="flex items-center justify-between gap-3">
                <dt className="text-label text-muted-foreground">
                  Manipulation risk (Beneish M)
                </dt>
                <dd>
                  <Badge variant={toneFor(manipulationRisk)}>
                    {manipulationRisk}
                  </Badge>
                </dd>
              </div>

              <div className="flex items-center justify-between gap-3 border-t border-border pt-2.5">
                <dt className="text-label text-muted-foreground">
                  Piotroski F-Score
                </dt>
                <dd className="text-label font-medium text-foreground">
                  {piotroskiRead}
                </dd>
              </div>
            </dl>
          </div>
        </ChartFrame>
      </div>
    </section>
  );
}
