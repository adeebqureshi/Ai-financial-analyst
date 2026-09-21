"use client";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard, formatRatio } from "@/components/ui/metric";
import { Badge, type BadgeProps } from "@/components/ui/badge";

type Props = {
  score: number;
  rating: string;
  piotroski: number;
  altman: number;
  beneish: number;
};

/**
 * Standard academic interpretation thresholds for the two backend scores:
 * Altman Z > 3 safe / 1.8-3 grey / < 1.8 distress, and Beneish M > -1.78
 * flags possible manipulation. They are applied to real backend scores and
 * labelled as interpretations of those scores.
 */
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
    <section data-testid="financial-health" aria-labelledby="health-heading">
      <div className="mb-4">
        <h2 id="health-heading" className="text-title text-foreground">
          Financial health
        </h2>
        <p className="mt-1 text-label text-muted-foreground">
          Backend quality scores and their standard interpretation.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Health score"
          value={`${score}/100`}
          hint={rating}
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

      <Card className="mt-4">
        <CardHeader>
          <CardTitle as="h3">Score interpretation</CardTitle>
          <span className="text-caption text-subtle-foreground">
            Derived from the values above
          </span>
        </CardHeader>

        <CardBody>
          <dl className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
            <div className="flex items-center justify-between gap-3 border-b border-border py-2">
              <dt className="text-label text-muted-foreground">
                Health rating
              </dt>
              <dd className="text-label font-medium text-foreground">
                {rating}
              </dd>
            </div>

            <div className="flex items-center justify-between gap-3 border-b border-border py-2">
              <dt className="text-label text-muted-foreground">
                Bankruptcy risk (Altman Z)
              </dt>
              <dd>
                <Badge variant={toneFor(bankruptcyRisk)}>{bankruptcyRisk}</Badge>
              </dd>
            </div>

            <div className="flex items-center justify-between gap-3 border-b border-border py-2">
              <dt className="text-label text-muted-foreground">
                Earnings manipulation risk (Beneish M)
              </dt>
              <dd>
                <Badge variant={toneFor(manipulationRisk)}>
                  {manipulationRisk}
                </Badge>
              </dd>
            </div>

            <div className="flex items-center justify-between gap-3 border-b border-border py-2">
              <dt className="text-label text-muted-foreground">
                Piotroski F-Score
              </dt>
              <dd className="text-label font-medium text-foreground">
                {piotroskiRead}
              </dd>
            </div>
          </dl>
        </CardBody>
      </Card>
    </section>
  );
}