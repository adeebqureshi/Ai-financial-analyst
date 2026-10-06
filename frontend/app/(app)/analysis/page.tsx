"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

import { AnalysisCapabilities } from "@/components/analysis/analysis-capabilities";
import { RecentAnalyses } from "@/components/analysis/recent-analyses";
import { CompanySearch } from "@/components/company/company-search";
import { TickerChip } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { resolveCompany } from "@/lib/companies";
import {
  POPULAR_TICKERS,
  TickerExamplesMenu,
} from "@/components/ui/ticker-lookup";

/**
 * The Analyze page has one job: get a ticker into the pipeline.
 *
 * Everything above the input was cut back to a single sentence, and the
 * capability set moved to a compact row underneath it. There is no hero
 * artwork and no sample-analysis link, because both competed with the primary
 * action and the popular chips already cover the shortcut the link provided.
 */
export default function AnalysisPage() {
  const router = useRouter();
  const [input, setInput] = useState("");

  const resolved = resolveCompany(input);
  const valid = resolved !== null;

  function submit() {
    const company = resolveCompany(input);
    if (!company) return;
    router.push(`/analysis/${company.ticker}`);
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 pb-8">
      <PageHeader
        eyebrow="Company Analysis"
        title="Analyze a company"
        description="Valuation, financial health, risk and AI insights for any public company."
        compact
      />

      <section aria-labelledby="analyze-heading">
        <h2 id="analyze-heading" className="sr-only">
          Start an analysis
        </h2>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
          className="rounded-xl border border-border bg-card p-2 shadow-card transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20"
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="flex min-w-0 flex-1 items-center gap-2.5 px-2">
              <CompanySearch
                value={input}
                onValueChange={setInput}
                onSelect={(company) => router.push(`/analysis/${company.ticker}`)}
                placeholder="Search company or ticker (e.g. NVIDIA or NVDA)"
                ariaLabel="Search company or ticker to analyze"
                autoFocus
                inputClassName="h-12 text-body"
              />
            </div>

            <Button
              type="submit"
              size="lg"
              disabled={!valid}
              className="h-12 w-full shrink-0 rounded-lg px-6 sm:w-auto"
            >
              Analyze
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </form>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2">
          <span className="text-caption text-subtle-foreground">Popular</span>

          {POPULAR_TICKERS.map((suggestion) => (
            <TickerChip
              key={suggestion}
              value={suggestion}
              onClick={() => setInput(suggestion)}
              title={`Analyze ${suggestion}`}
            />
          ))}

          <TickerExamplesMenu onSelect={setInput} className="ml-auto" />
        </div>
      </section>

      <AnalysisCapabilities />

      <RecentAnalyses />
    </div>
  );
}