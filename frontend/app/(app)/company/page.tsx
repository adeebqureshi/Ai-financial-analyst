"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Building2, Search, Sparkles } from "lucide-react";

import { CompanyCapabilities } from "@/components/company/company-capabilities";
import { CompanyHero } from "@/components/company/company-hero";
import { TickerChip } from "@/components/ui/badge";
import { Button, TextAction } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { TickerInput } from "@/components/ui/field";
import {
  POPULAR_TICKERS,
  TickerExamplesMenu,
} from "@/components/ui/ticker-lookup";

const SYMBOL_PATTERN = /^[A-Z]{1,5}$/;

export default function CompanyPage() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");

  const symbol = ticker.trim().toUpperCase();
  const valid = SYMBOL_PATTERN.test(symbol);

  function submit() {
    if (!valid) return;

    router.push(`/company/${symbol}`);
  }

  return (
    <div className="mx-auto flex max-w-[84rem] flex-col gap-6 pb-8">
      <CompanyHero />

      <section
        aria-labelledby="company-lookup-heading"
        className="rounded-2xl border border-border bg-card p-5 shadow-card sm:p-6"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <span
              className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-subtle text-brand"
              aria-hidden="true"
            >
              <Building2 size={19} />
            </span>

            <div className="min-w-0">
              <h2
                id="company-lookup-heading"
                className="text-subtitle text-foreground"
              >
                Look up a company
              </h2>
              <p className="mt-1 max-w-xl text-label text-muted-foreground">
                Enter a ticker symbol to open its profile and run the full AI
                analysis.
              </p>
            </div>
          </div>

          <TickerExamplesMenu
            onSelect={setTicker}
            className="max-sm:hidden"
          />
        </div>

        <form
          className="mt-5"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          {/* The field and the CTA share one surface: the symbol is the focus
              of the workflow, so the primary action sits inside its right
              edge and wraps below only when the viewport is too narrow. */}
          <div className="flex flex-col gap-2 rounded-xl border border-input bg-background p-1.5 pl-4 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20 sm:flex-row sm:items-center">
            <div className="flex min-w-0 items-center gap-3">
              <Search
                size={18}
                className="shrink-0 text-brand"
                aria-hidden="true"
              />

              <TickerInput
                value={ticker}
                onValueChange={setTicker}
                placeholder="Enter ticker (e.g., AAPL, MSFT, NVDA)"
                aria-label="Ticker symbol to look up"
                className="h-11 min-w-0 flex-1 border-0 bg-transparent px-0 pr-3 text-body focus-visible:border-0 focus-visible:ring-0"
              />
            </div>

            <Button
              type="submit"
              size="lg"
              disabled={!valid}
              className="h-11 w-full shrink-0 rounded-lg px-5 sm:ml-auto sm:w-auto"
            >
              Open profile
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </form>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-label font-medium text-muted-foreground">
            Popular
          </span>

          {POPULAR_TICKERS.map((suggestion) => (
            <TickerChip
              key={suggestion}
              value={suggestion}
              onClick={() => setTicker(suggestion)}
              title={`Use ${suggestion}`}
            />
          ))}
        </div>
      </section>

      <CompanyCapabilities />

      {/* No company is selected until the user looks one up, and nothing here
          is cached from a previous session — so this is a genuine empty state
          rather than a placeholder for data the workspace does not have. */}
      <EmptyState
        icon={<Building2 size={20} aria-hidden="true" />}
        tone="brand"
        title="No company directory in this workspace"
        description="Look up a symbol above to view its profile, then run an AI analysis from there."
        action={
          <TextAction
            href="/analysis"
            icon={<Sparkles size={14} aria-hidden="true" />}
            arrow
          >
            Go to analysis
          </TextAction>
        }
      />
    </div>
  );
}
