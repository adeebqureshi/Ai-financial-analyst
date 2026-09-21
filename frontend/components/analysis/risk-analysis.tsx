"use client";

import { Loader2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard, formatRatio } from "@/components/ui/metric";
import type { RiskAssessmentData } from "@/types/analysis";

type Props = {
  /** Real beta from the `/analyze` market snapshot; null when unavailable. */
  beta: number | null;
  /** Real risk assessment from `POST /risk-analysis`. */
  risk: RiskAssessmentData | null;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
};

/**
 * Renders only what the backend actually returns: the health score, rating,
 * risk level, and the individual score details. Volatility and business /
 * financial risk percentages are intentionally absent — no endpoint provides
 * them and the UI must not fabricate them.
 */
export function RiskAnalysis({
  beta,
  risk,
  isLoading,
  isError,
  onRetry,
}: Props) {
  function formatScoreDetail(
    detail: Record<string, unknown>
  ): { label: string; value: string }[] {
    return Object.entries(detail)
      .filter(
        (entry): entry is [string, string | number | boolean] =>
          typeof entry[1] === "string" ||
          typeof entry[1] === "number" ||
          typeof entry[1] === "boolean"
      )
      .map(([label, value]) => ({
        label,
        value: typeof value === "boolean" ? (value ? "Yes" : "No") : String(value),
      }));
  }

  const unavailable = "Not available from the market data provider";

  return (
    <section
      data-testid="risk-analysis"
      aria-labelledby="risk-heading"
    >
      <div className="mb-4">
        <h2 id="risk-heading" className="text-title text-foreground">
          Risk analysis
        </h2>
        <p className="mt-1 text-label text-muted-foreground">
          Quantitative risk and health assessment from the backend.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Beta"
          value={beta === null ? "—" : formatRatio(beta)}
          hint={beta === null ? unavailable : "Market sensitivity"}
        />

        <MetricCard
          label="Health score"
          value={risk ? `${risk.health_score}/100` : "—"}
          hint={risk?.health_rating ?? "Waiting for risk assessment"}
        />

        <MetricCard
          label="Risk level"
          value={risk?.risk_level ?? "—"}
          hint="Overall backend assessment"
        />

        <MetricCard
          label="Piotroski F-Score"
          value={
            risk && typeof risk.piotroski?.score === "number"
              ? `${risk.piotroski.score}/9`
              : "—"
          }
          hint="Financial strength"
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {(
          [
            ["Altman Z-Score", risk?.altman],
            ["Beneish M-Score", risk?.beneish],
          ] as const
        ).map(([title, detail]) => (
          <Card key={title}>
            <CardHeader>
              <CardTitle as="h3">{title}</CardTitle>
            </CardHeader>

            <CardBody>
              {detail ? (
                <dl>
                  {formatScoreDetail(detail).map((row) => (
                    <div
                      key={row.label}
                      className="flex items-center justify-between gap-4 border-b border-border py-2.5 last:border-0"
                    >
                      <dt className="text-label text-muted-foreground">
                        {row.label}
                      </dt>
                      <dd className="tnum text-label font-medium text-foreground">
                        {row.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <p className="text-label text-subtle-foreground">
                  Detail unavailable.
                </p>
              )}
            </CardBody>
          </Card>
        ))}
      </div>

      {isLoading && (
        <p
          role="status"
          className="mt-4 inline-flex items-center gap-2 text-label text-muted-foreground"
        >
          <Loader2
            size={16}
            className="motion-safe:animate-spin"
            aria-hidden="true"
          />
          Loading risk assessment…
        </p>
      )}

      {isError && (
        <div
          role="alert"
          className="mt-4 flex flex-wrap items-center gap-3 rounded-lg border border-loss/30 bg-loss-subtle px-4 py-3"
        >
          <p className="text-label text-loss">
            Risk assessment is currently unavailable.
          </p>

          <Button variant="secondary" size="sm" onClick={onRetry}>
            <RotateCcw size={14} aria-hidden="true" />
            Try again
          </Button>
        </div>
      )}
    </section>
  );
}
