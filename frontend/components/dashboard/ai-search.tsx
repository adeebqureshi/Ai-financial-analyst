"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CornerDownLeft, Loader2, Search, Sparkles } from "lucide-react";

import { useAnalysis } from "@/hooks/use-analysis";
import { useCopilot } from "@/components/layout/ai-copilot";
import { ErrorInline } from "@/components/ui/error-display";
import { TickerChip } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const TICKER_PATTERN = /^[A-Z]{1,5}$/;

const suggestions = [
  { label: "AAPL", hint: "Analyze a company" },
  { label: "NVDA", hint: "Valuation and risk" },
  { label: "MSFT", hint: "Financial health" },
  { label: "What are the key risks disclosed in this quarter's filings?", hint: "Ask a question" },
];

export function AISearch() {
  const router = useRouter();
  const copilot = useCopilot();

  const [query, setQuery] = useState("");
  const [error, setError] = useState<unknown>(null);

  const analysis = useAnalysis();
  const symbol = query.trim().toUpperCase();
  const isTicker = TICKER_PATTERN.test(symbol);
  const busy = analysis.isPending;

  async function runTicker(next: string) {
    const target = next.trim().toUpperCase();

    if (!TICKER_PATTERN.test(target)) {
      setError(new Error("Enter a ticker symbol of 1–5 letters to analyze."));
      return;
    }

    setError(null);

    try {
      await analysis.mutateAsync(target);
      router.push(`/analysis/${target}`);
    } catch (err) {
      setError(err);
    }
  }

  function submit() {
    if (!symbol || busy) return;

    if (isTicker) {
      void runTicker(symbol);
      return;
    }

    setError(null);
    copilot.open({ prompt: query.trim() });
  }

  return (
    <section
      data-testid="ai-search"
      aria-labelledby="ai-search-heading"
      className="overflow-hidden rounded-2xl border border-border bg-card shadow-card"
    >
      <div className="px-5 pb-5 pt-6 sm:px-7 sm:pb-6 sm:pt-7">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 rounded-full border border-brand/25 bg-brand-subtle px-2.5 py-0.5 text-caption font-medium text-brand"
            aria-hidden="true"
          >
            <Sparkles size={12} />
            AI copilot
          </span>
          <h2
            id="ai-search-heading"
            className="text-title text-foreground"
          >
            Ask AI about any public company
          </h2>
        </div>

        <p className="mt-2 max-w-2xl text-label text-muted-foreground">
          Enter a ticker to run the full AI pipeline — valuation, financial
          health, intrinsic value and risk. Anything longer is sent to the
          copilot as a research question.
        </p>

        <form
          className="mt-5"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <div
            className={cn(
              "flex items-center gap-3 rounded-xl border bg-background px-4",
              "transition-[border-color,box-shadow] duration-150",
              "focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20"
            )}
          >
            <Search
              size={19}
              className="shrink-0 text-brand"
              aria-hidden="true"
            />

            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setError(null);
              }}
              placeholder="Enter ticker (AAPL, MSFT, NVDA…) or ask a research question"
              aria-label="Ticker to analyze or question for the AI copilot"
              autoComplete="off"
              spellCheck={false}
              className="h-14 min-w-0 flex-1 bg-transparent text-body text-foreground outline-none placeholder:text-subtle-foreground"
            />

            <button
              type="submit"
              disabled={!symbol || busy}
              aria-label={isTicker ? `Analyze ${symbol}` : "Ask the copilot"}
              className={cn(
                "inline-flex size-9 shrink-0 items-center justify-center rounded-lg",
                "transition-colors duration-150",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                symbol
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {busy ? (
                <Loader2
                  size={17}
                  className="motion-safe:animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <CornerDownLeft size={17} aria-hidden="true" />
              )}
            </button>
          </div>
        </form>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-caption text-subtle-foreground">Try</span>

          {suggestions.map((suggestion) =>
            suggestion.label.length <= 5 ? (
              <TickerChip
                key={suggestion.label}
                value={suggestion.label}
                title={suggestion.hint}
                onClick={() => setQuery(suggestion.label)}
              />
            ) : (
              <button
                key={suggestion.label}
                type="button"
                onClick={() => setQuery(suggestion.label)}
                title={suggestion.hint}
                className="max-w-full truncate rounded-md border border-border bg-surface px-2.5 py-1.5 text-caption text-muted-foreground transition-colors hover:border-border-strong hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                {suggestion.label}
              </button>
            )
          )}
        </div>

        {error !== null && (
          <div className="mt-4" role="alert" aria-live="polite">
            <ErrorInline error={error} onRetry={() => void runTicker(symbol)} />
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-1.5 border-t border-border bg-surface/60 px-5 py-3 text-caption text-muted-foreground sm:px-7">
        <span>Enter runs the analysis pipeline</span>
        <span aria-hidden="true" className="text-muted-foreground">
          ·
        </span>
        <span>Press Ctrl + K anywhere for the command palette</span>
      </div>
    </section>
  );
}
