"use client";

import { useState } from "react";
import { FileText, Loader2, Sparkles } from "lucide-react";

import { api } from "@/services/api";
import { ReportViewer } from "@/components/analysis/report-viewer";
import { SectionHeading } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonRows } from "@/components/ui/skeleton";

import type { ApiResponse, ReportData } from "@/types/analysis";

type Props = {
  /** The ticker under analysis. Generation is never automatic: it costs an LLM
      call and roughly a minute of backend work, so the user asks for it. */
  ticker: string;
};

const GENERATION_STEPS = [
  "Gathering market data and filings",
  "Running the valuation model",
  "Writing the research narrative",
];

/**
 * Report generation as the closing step of a company analysis.
 *
 * This is the same capability the standalone Reports page exposed — the same
 * `POST /report` call, the same long timeout, the same `ReportViewer` — bound to
 * the ticker already being analysed instead of asking for one again.
 */
export function ReportPanel({ ticker }: Props) {
  const [report, setReport] = useState<ReportData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function generate() {
    if (generating) return;

    setGenerating(true);
    setError(null);
    setReport(null);

    try {
      const response = await api.report({ ticker });

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

  return (
    <section id="report" className="space-y-5 scroll-mt-32">
      <SectionHeading
        title="Research report"
        description={`Generate an LLM research report for ${ticker}, grounded in the same market data and documents as this analysis. This can take a while.`}
      />

      {!report && !generating && error === null && (
        <EmptyState
          compact
          tone="brand"
          icon={<Sparkles size={20} aria-hidden="true" />}
          title="No report yet"
          description="Generate a detailed research write-up for this company to read alongside the analysis above."
          action={
            <Button onClick={() => void generate()}>
              <Sparkles size={16} aria-hidden="true" />
              Generate report
            </Button>
          }
        />
      )}

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
                <Loader2 size={16} className="motion-safe:animate-spin" />
              </span>
              <p className="text-label font-medium text-foreground">
                Researching {ticker}…
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

      {report && (
        <div className="space-y-4">
          <div>
            <p className="text-caption font-semibold uppercase tracking-[0.12em] text-brand">
              {report.ticker} · {report.format}
            </p>
            <h3 className="mt-2 text-balance text-title text-foreground">
              {report.title}
            </h3>
          </div>

          <ReportViewer report={report.content} />
        </div>
      )}

      {report && (
        <Button variant="ghost" onClick={() => setReport(null)}>
          <FileText size={16} aria-hidden="true" />
          Generate a new report
        </Button>
      )}
    </section>
  );
}