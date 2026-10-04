"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Search } from "lucide-react";

import { AnalysisCapabilities } from "@/components/analysis/analysis-capabilities";
import { RecentAnalyses } from "@/components/analysis/recent-analyses";
import { TickerChip } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TickerInput } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import {
  POPULAR_TICKERS,
  TickerExamplesMenu,
} from "@/components/ui/ticker-lookup";

const SYMBOL_PATTERN = /^[A-Z]{1,5}$/;

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
  const [ticker, setTicker] = useState("");

  const symbol = ticker.trim().toUpperCase();
  const valid = SYMBOL_PATTERN.test(symbol);

  function submit() {
    if (!SYMBOL_PATTERN.test(symbol)) return;

    router.push(`/analysis/${symbol}`);
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
              <Search
                size={18}
                className="shrink-0 text-brand"
                aria-hidden="true"
              />

              <TickerInput
                value={ticker}
                onValueChange={setTicker}
                placeholder="Enter ticker (e.g. NVDA)"
                aria-label="Ticker symbol to analyze"
                autoFocus
                className="h-12 min-w-0 flex-1 border-0 bg-transparent px-0 text-body focus-visible:border-0 focus-visible:ring-0"
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
              onClick={() => setTicker(suggestion)}
              title={`Analyze ${suggestion}`}
            />
          ))}

          <TickerExamplesMenu onSelect={setTicker} className="ml-auto" />
        </div>
      </section>

      <AnalysisCapabilities />

      <RecentAnalyses />
    </div>
  );
}