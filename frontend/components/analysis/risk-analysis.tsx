"use client";

import { Loader2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
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

  return (

    <section data-testid="risk-analysis" aria-live="polite">

      <div className="mb-8">

        <h2 className="text-3xl font-bold text-white">
          Risk Analysis
        </h2>

        <p className="mt-2 text-zinc-500">
          Quantitative risk and health assessment
        </p>

      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">

          <p className="text-sm text-zinc-500">
            Beta
          </p>

          <h2 className="mt-3 text-4xl font-bold text-white">
            {beta === null ? "—" : beta.toFixed(2)}
          </h2>

          <p className="mt-3 text-sm text-zinc-500">
            {beta === null
              ? "Not available from the market data provider"
              : "Market sensitivity"}
          </p>

        </div>

        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">

          <p className="text-sm text-zinc-500">
            Health Score
          </p>

          <h2 className="mt-3 text-4xl font-bold text-white">
            {risk ? `${risk.health_score}/100` : "—"}
          </h2>

          <p className="mt-3 text-sm text-zinc-500">
            {risk?.health_rating ?? "Waiting for risk assessment"}
          </p>

        </div>

        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">

          <p className="text-sm text-zinc-500">
            Risk Level
          </p>

          <h2 className="mt-3 text-4xl font-bold text-white">
            {risk?.risk_level ?? "—"}
          </h2>

          <p className="mt-3 text-sm text-zinc-500">
            Overall assessment
          </p>

        </div>

        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">

          <p className="text-sm text-zinc-500">
            Piotroski F Score
          </p>

          <h2 className="mt-3 text-4xl font-bold text-white">
            {risk &&
            typeof risk.piotroski?.score === "number"
              ? `${risk.piotroski.score}/9`
              : "—"}
          </h2>

          <p className="mt-3 text-sm text-zinc-500">
            Financial strength
          </p>

        </div>

      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">

        {(
          [
            ["Altman Z-Score", risk?.altman],
            ["Beneish M-Score", risk?.beneish],
          ] as const
        ).map(([title, detail]) => (

          <div
            key={title}
            className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6"
          >

            <h3 className="text-xl font-semibold text-white">
              {title}
            </h3>

            {detail ? (

              <dl className="mt-4">
                {formatScoreDetail(detail).map((row) => (

                  <div
                    key={row.label}
                    className="flex items-center justify-between border-b border-white/5 py-3 last:border-0"
                  >

                    <dt className="text-sm text-zinc-400">
                      {row.label}
                    </dt>

                    <dd className="font-semibold text-white">
                      {row.value}
                    </dd>

                  </div>

                ))}
              </dl>

            ) : (

              <p className="mt-4 text-sm text-zinc-500">
                Detail unavailable.
              </p>

            )}

          </div>

        ))}

      </div>

      {isLoading && (
        <p className="mt-8 inline-flex items-center gap-2 text-sm text-zinc-400">
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
          className="mt-8 flex flex-wrap items-center gap-4 rounded-2xl border border-red-500/25 bg-red-500/10 px-6 py-4"
        >
          <p className="text-sm text-red-300">
            Risk assessment is currently unavailable.
          </p>

          <Button
            variant="secondary"
            size="sm"
            onClick={onRetry}
          >
            <RotateCcw size={14} aria-hidden="true" />
            Try again
          </Button>
        </div>
      )}

    </section>

  );
}
