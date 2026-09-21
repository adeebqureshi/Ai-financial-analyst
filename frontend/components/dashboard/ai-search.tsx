"use client";

import { ArrowRight, Search } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalysis } from "@/hooks/use-analysis";
import { ErrorInline } from "@/components/ui/error-display";
import { Card } from "@/components/ui/card";

const suggestions = [
  "AAPL",
  "MSFT",
  "NVDA",
  "TSLA",
  "AMZN",
  "GOOGL",
];

export function AISearch() {
  const router = useRouter();

  const [ticker, setTicker] = useState("");
  const [error, setError] = useState<unknown>(null);

  const analysis = useAnalysis();

  async function submit() {
    const symbol = ticker.trim().toUpperCase();

    if (!symbol) {
      setError(new Error("Enter a ticker symbol to analyze."));
      return;
    }

    setError(null);

    try {
      await analysis.mutateAsync(symbol);
      router.push(`/analysis/${symbol}`);
    } catch (err) {
      setError(err);
    }
  }

  return (
    <Card className="p-6 sm:p-8" data-testid="ai-search">
      <h2 className="text-title text-foreground">
        Ask AI about any public company.
      </h2>

      <p className="mt-2 max-w-3xl text-body text-muted-foreground">
        Enter a ticker to run the full AI pipeline — valuation, financial
        health, intrinsic value and risk analysis from the backend.
      </p>

      <form
        className="mt-6 flex flex-col gap-3 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <div className="flex min-w-0 flex-1 items-center gap-2 rounded-md border border-input bg-card px-3 focus-within:border-border-strong focus-within:ring-2 focus-within:ring-ring">
          <Search className="shrink-0 text-muted-foreground" size={18} aria-hidden="true" />

          <input
            value={ticker}
            onChange={(event) => setTicker(event.target.value)}
            placeholder="Enter ticker (AAPL, MSFT, NVDA...)"
            aria-label="Ticker symbol to analyze"
            autoComplete="off"
            spellCheck={false}
            maxLength={5}
            className="h-11 min-w-0 flex-1 bg-transparent text-body text-foreground outline-none placeholder:text-subtle-foreground"
          />
        </div>

        <button
          type="submit"
          disabled={analysis.isPending}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-brand px-5 text-label font-medium text-brand-foreground transition-colors hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          {analysis.isPending ? "Analyzing…" : "Analyze"}
          {!analysis.isPending && (
            <ArrowRight className="size-4" aria-hidden="true" />
          )}
        </button>
      </form>

      <div className="mt-4 flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => setTicker(suggestion)}
            className="rounded-full border border-border bg-muted px-3 py-1 font-mono text-caption text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {error !== null && (
        <div className="mt-6" role="alert" aria-live="polite">
          <ErrorInline error={error} onRetry={() => void submit()} />
        </div>
      )}
    </Card>
  );
}