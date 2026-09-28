"use client";

import { Loader2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard, formatRatio } from "@/components/ui/metric";
import { SectionHeading } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import type { RiskAssessmentData } from "@/types/analysis";

import { ChartFrame } from "./visuals";

type Props = {
  beta: number | null;

  risk: RiskAssessmentData | null;

  isLoading: boolean;

  isError: boolean;

  onRetry: () => void;
};

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
        value:
          typeof value === "boolean"
            ? value
              ? "Yes"
              : "No"
            : typeof value === "number"
              ? Number.isInteger(value)
                ? value.toLocaleString("en-US")
                : String(Number(value.toFixed(4)))
              : String(value),
      }));
  }

  const unavailable = "Not available from the market data provider";

  return (
    <section
      id="risk"
      data-testid="risk-analysis"
      aria-labelledby="risk-heading"
      className="space-y-5 scroll-mt-32"
    >
      <SectionHeading
        id="risk-heading"
        title="Risk analysis"
        description="Quantitative risk and health assessment from the backend."
      />

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

      <div className="grid gap-4 lg:grid-cols-2">
        {(
          [
            ["Altman Z-Score", risk?.altman],
            ["Beneish M-Score", risk?.beneish],
          ] as const
        ).map(([title, detail]) => (
          <ChartFrame key={title} title={title} description="Component detail">
            {isLoading ? (
              <div className="space-y-3" aria-hidden="true">
                {[0, 1, 2].map((index) => (
                  <Skeleton key={index} className="h-4 w-full" />
                ))}
              </div>
            ) : detail ? (
              <dl>
                {formatScoreDetail(detail).map((row) => (
                  <div
                    key={row.label}
                    className="flex items-baseline justify-between gap-4 border-b border-border py-2.5 last:border-0"
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
          </ChartFrame>
        ))}
      </div>

      {isLoading && (
        <p
          role="status"
          className="inline-flex items-center gap-2 text-label text-muted-foreground"
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
          className="flex flex-wrap items-center gap-3 rounded-xl border border-loss/30 bg-loss-subtle px-4 py-3"
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
