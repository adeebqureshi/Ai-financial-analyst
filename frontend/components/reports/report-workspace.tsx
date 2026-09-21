"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";

import { api } from "@/services/api";
import { ReportViewer } from "@/components/analysis/report-viewer";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { Field, TickerInput } from "@/components/ui/field";
import { SkeletonCard } from "@/components/ui/skeleton";

import type { ApiResponse, ReportData } from "@/types/analysis";

const suggestions = [
  "AAPL",
  "MSFT",
  "NVDA",
  "TSLA",
  "AMZN",
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
      <Card aria-labelledby="report-form-heading">
        <CardHeader>
          <div>
            <CardTitle as="h2" id="report-form-heading">
              Generate a report
            </CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              The backend researches the company and writes the report; this can
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
              className="sm:max-w-40"
            >
              <TickerInput
                id="report-ticker"
                value={ticker}
                onValueChange={setTicker}
                placeholder="AAPL"
              />
            </Field>

            <Button type="submit" disabled={!valid || generating}>
              <Sparkles size={16} aria-hidden="true" />
              {generating ? "Generating…" : "Generate report"}
            </Button>
          </form>

          <div className="mt-4 flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setTicker(suggestion);
                  setReport(null);
                }}
                className="rounded-full border border-border bg-muted px-3 py-1 font-mono text-caption text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      {error !== null && (
        <ErrorDisplay error={error} onRetry={() => void generate()} />
      )}

      {generating && (
        <div role="status" aria-busy="true">
          <SkeletonCard />
          <span className="sr-only">Generating report…</span>
        </div>
      )}

      {!generating && error === null && !report && (
        <EmptyState
          icon={<Sparkles size={20} aria-hidden="true" />}
          title="No report yet"
          description="Enter a ticker symbol and generate a report to see the research here."
        />
      )}

      {report && (
        <section aria-labelledby="report-title">
          <h2 id="report-title" className="text-title text-foreground">
            {report.title}
          </h2>
          <div className="mt-4">
            <ReportViewer report={report.content} />
          </div>
        </section>
      )}
    </div>
  );
}
