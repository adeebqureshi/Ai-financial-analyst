"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Search, Sparkles } from "lucide-react";

import { TickerInput } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import { Button, TextAction } from "@/components/ui/button";
import { TickerChip } from "@/components/ui/badge";

const suggestions = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA"];

export default function AnalysisPage() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");

  const symbol = ticker.trim().toUpperCase();
  const valid = /^[A-Z]{1,5}$/.test(symbol);

  function submit() {
    if (!/^[A-Z]{1,5}$/.test(symbol)) return;

    router.push(`/analysis/${symbol}`);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-10 pb-8">
      <PageHeader
        eyebrow="Company & Valuation"
        title="Company analysis"
        description="Run the full AI pipeline for any public company — valuation, financial health, intrinsic value, risk and a grounded copilot."
      />

      <section
        aria-labelledby="analysis-lookup-heading"
        className="overflow-hidden rounded-2xl border border-border bg-card shadow-card"
      >
        <div className="px-5 py-6 sm:px-7 sm:py-7">
          <h2
            id="analysis-lookup-heading"
            className="flex items-center gap-2 text-subtitle text-foreground"
          >
            <Sparkles size={16} className="text-brand" aria-hidden="true" />
            Start with a ticker
          </h2>

          <p className="mt-2 max-w-xl text-label text-muted-foreground">
            Enter a 1–5 letter symbol. The backend runs market data, the DCF
            valuation and the health scores before the workspace renders.
          </p>

          <form
            className="mt-6"
            onSubmit={(event) => {
              event.preventDefault();
              submit();
            }}
          >
            {/* Input and action form a single surface: the field is the focus
                of the workflow and the CTA sits inside its right edge. It
                wraps below the input only when the viewport is too narrow. */}
            <div className="flex flex-col gap-2 rounded-lg border border-input bg-background p-1.5 pl-4 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20 sm:flex-row sm:items-center">
              <div className="flex min-w-0 items-center gap-3">
                <Search
                  size={17}
                  className="shrink-0 text-brand"
                  aria-hidden="true"
                />

                <TickerInput
                  value={ticker}
                  onValueChange={setTicker}
                  placeholder="Enter ticker (AAPL, MSFT, NVDA…)"
                  aria-label="Ticker symbol to analyze"
                  className="h-10 min-w-0 flex-1 border-0 bg-transparent px-0 text-body focus-visible:border-0 focus-visible:ring-0"
                />
              </div>

              <Button
                type="submit"
                disabled={!valid}
                className="w-full shrink-0 sm:ml-auto sm:w-auto"
              >
                Analyze
                <ArrowRight size={15} aria-hidden="true" />
              </Button>
            </div>
          </form>

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className="text-caption text-subtle-foreground">Popular</span>

            {suggestions.map((suggestion) => (
              <TickerChip
                key={suggestion}
                value={suggestion}
                onClick={() => setTicker(suggestion)}
                title={`Use ${suggestion}`}
              />
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-1.5 border-t border-border bg-surface/60 px-5 py-3 text-caption text-muted-foreground sm:px-7">
          <span>Valuation, health, market and risk in one workspace</span>
          <span aria-hidden="true" className="text-muted-foreground">
            ·
          </span>
          <TextAction href="/dashboard">
            Or start from the Command Hub
          </TextAction>
        </div>
      </section>
    </div>
  );
}
