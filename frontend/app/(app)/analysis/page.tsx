"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Search, Sparkles } from "lucide-react";

import { TickerInput } from "@/components/ui/field";
import { PageHeader } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";

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
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="flex min-w-0 flex-1 items-center gap-3 rounded-xl border border-input bg-background px-4 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20">
                <Search
                  size={18}
                  className="shrink-0 text-brand"
                  aria-hidden="true"
                />

                <TickerInput
                  value={ticker}
                  onValueChange={setTicker}
                  placeholder="Enter ticker (AAPL, MSFT, NVDA…)"
                  aria-label="Ticker symbol to analyze"
                  className="h-14 border-0 bg-transparent px-0 text-body focus-visible:border-0 focus-visible:ring-0"
                />
              </div>

              <Button type="submit" size="xl" disabled={!valid}>
                Analyze
                <ArrowRight size={17} aria-hidden="true" />
              </Button>
            </div>
          </form>

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className="text-caption text-subtle-foreground">Popular</span>

            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setTicker(suggestion)}
                className="rounded-full border border-border bg-surface px-3 py-1 font-mono text-caption font-medium tracking-[0.04em] text-muted-foreground transition-colors hover:border-border-strong hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-1.5 border-t border-border bg-surface/60 px-5 py-3 text-caption text-muted-foreground sm:px-7">
          <span>Valuation, health, market and risk in one workspace</span>
          <span aria-hidden="true" className="text-border-strong">
            ·
          </span>
          <Link
            href="/dashboard"
            className="font-medium text-brand underline-offset-4 hover:underline"
          >
            Or start from the Command Hub
          </Link>
        </div>
      </section>
    </div>
  );
}
