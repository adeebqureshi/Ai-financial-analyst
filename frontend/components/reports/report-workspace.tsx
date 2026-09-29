"use client";

import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { api } from "@/services/api";
import { ReportViewer } from "@/components/analysis/report-viewer";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { Field, TickerInput } from "@/components/ui/field";
import { TickerChip } from "@/components/ui/badge";
import { SkeletonRows } from "@/components/ui/skeleton";

import type { ApiResponse, ReportData } from "@/types/analysis";

const suggestions = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"];

const GENERATION_STEPS = [
  "Gathering market data and filings",
  "Running the valuation model",
  "Writing the research narrative",
];

export function ReportWorkspace() {
  const [ticker, setTicker] = useState("");
  const [report, setReport] = useState<ReportData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function generate() {
    const normalized = ticker.trim().toUpperCase();

    if (!/^[A-Z]{1,5}$/.test(normalized) || generating) {
      return;
    }

    setGenerating(true);
    setError(null);
    setReport(null);

    try {
      const response = await api.report({ ticker: normalized });

      const data = (response as ApiResponse<ReportData>).data;

      if (!data) {
        throw new Error("No report was generated.");
      }

      setReport(data);
    } catch (err) {
      setError(err);
    } finally {
      setGenerating(false);
    }
  }

  const valid = /^[A-Z]{1,5}$/.test(ticker.trim().toUpperCase());

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div>
            <CardTitle as="h2">Generate a report</CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              The backend researches the company and writes the report. This can
              take a while.
            </p>
          </div>
        </CardHeader>

        <CardBody>
          <form
            className="flex flex-col gap-3 sm:flex-row sm:items-end"
            onSubmit={(event) => {
              event.preventDefault();
              void generate();
            }}
          >
            <Field
              label="Ticker symbol"
              htmlFor="report-ticker"
              required
              className="sm:max-w-48"
            >
              <TickerInput
                id="report-ticker"
                value={ticker}
                onValueChange={setTicker}
                placeholder="AAPL"
                className="h-11"
              />
            </Field>

            <Button type="submit" disabled={!valid || generating}>
              {generating ? (
                <Loader2
                  size={16}
                  className="motion-safe:animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <Sparkles size={16} aria-hidden="true" />
              )}
              {generating ? "Generating…" : "Generate report"}
            </Button>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-caption text-subtle-foreground">Suggested</span>

            {suggestions.map((suggestion) => (
              <TickerChip
                key={suggestion}
                value={suggestion}
                title={`Use ${suggestion}`}
                onClick={() => {
                  setTicker(suggestion);
                  setReport(null);
                }}
              />
            ))}
          </div>
        </CardBody>
      </Card>

      {error !== null && (
        <ErrorDisplay error={error} onRetry={() => void generate()} />
      )}

      {generating && (
        <Card role="status" aria-busy="true">
          <CardBody className="space-y-5">
            <div className="flex items-center gap-3">
              <span
                className="flex size-8 items-center justify-center rounded-lg bg-brand-subtle text-brand"
                aria-hidden="true"
              >
                <Loader2
                  size={16}
                  className="motion-safe:animate-spin"
                />
              </span>
              <p className="text-label font-medium text-foreground">
                Researching {ticker.trim().toUpperCase()}…
              </p>
            </div>

            <ol className="space-y-2.5">
              {GENERATION_STEPS.map((step, index) => (
                <li
                  key={step}
                  className="flex items-center gap-2.5 text-label text-muted-foreground"
                >
                  <span
                    className="tnum flex size-5 items-center justify-center rounded-full border border-border bg-surface text-[11px] font-medium text-subtle-foreground"
                    aria-hidden="true"
                  >
                    {index + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>

            <SkeletonRows rows={3} />
          </CardBody>
        </Card>
      )}

      {!generating && error === null && !report && (
        <EmptyState
          tone="brand"
          icon={<Sparkles size={20} aria-hidden="true" />}
          title="No report yet"
          description="Enter a ticker symbol and generate a report to see the full research write-up here."
        />
      )}

      {report && (
        <section aria-labelledby="report-title" className="space-y-4">
          <div>
            <p className="text-caption font-semibold uppercase tracking-[0.12em] text-brand">
              {report.ticker} · {report.format}
            </p>
            <h2
              id="report-title"
              className="mt-2 text-balance text-title text-foreground"
            >
              {report.title}
            </h2>
          </div>

          <ReportViewer report={report.content} />
        </section>
      )}
    </div>
  );
}
