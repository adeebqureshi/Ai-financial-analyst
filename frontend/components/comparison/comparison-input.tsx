"use client";

import { GitCompare, Plus, Trash2, X } from "lucide-react";
import { useId, useState } from "react";

import { CompanyLogo } from "@/components/company/company-logo";
import { CompanySearch } from "@/components/company/company-search";
import { Button } from "@/components/ui/button";
import { resolveCompany } from "@/lib/companies";
import { cn } from "@/lib/utils";

/**
 * Shortcuts into the ticker input.
 *
 * Symbols only — the registry in `@/lib/company-logos` owns identity and logos,
 * so this list never needs editing when a logo or company name changes.
 */
const POPULAR_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA"];

const MAX_TICKERS = 10;

type Props = {
  tickers: string[];
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
  onClear: () => void;
  isLoading?: boolean;
  disabled?: boolean;
};

export function ComparisonInput({
  tickers,
  onAdd,
  onRemove,
  onClear,
  isLoading = false,
  disabled = false,
}: Props) {
  const inputId = useId();
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  const atLimit = tickers.length >= MAX_TICKERS;

  function add(raw: string) {
    const company = resolveCompany(raw);

    if (!company) {
      setError(
        raw.trim()
          ? "No matching company found. Select a company from the suggestions."
          : "Enter a company name or ticker to add.",
      );
      return;
    }

    const candidate = company.ticker;

    if (tickers.includes(candidate)) {
      setError(`${candidate} is already in the comparison.`);
      return;
    }

    if (atLimit) {
      setError(`You can compare up to ${MAX_TICKERS} companies at once.`);
      return;
    }

    setError(null);
    onAdd(candidate);
    setInput("");
  }

  return (
    <section
      aria-labelledby="comparison-input-heading"
      className="rounded-2xl border border-border bg-card px-4 py-5 shadow-card sm:px-6 sm:py-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-brand-subtle text-brand"
            aria-hidden="true"
          >
            <GitCompare size={18} />
          </span>

          <div className="min-w-0">
            <h2
              id="comparison-input-heading"
              className="text-subtitle font-semibold text-foreground"
            >
              Add companies to compare
            </h2>
            <p className="mt-1 text-label text-muted-foreground">
              Search by company name or ticker. Every value is computed by the
              backend{" "}
              <code className="rounded bg-muted px-1 font-mono text-caption text-foreground">
                /compare
              </code>{" "}
              endpoint.
            </p>
          </div>
        </div>

        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={onClear}
          disabled={disabled || tickers.length === 0}
          className="shrink-0"
        >
          <Trash2 size={14} aria-hidden="true" />
          Clear all
        </Button>
      </div>

      <form
        className="mt-4 flex flex-col gap-2.5 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          add(input);
        }}
      >
        <label htmlFor={inputId} className="sr-only">
          Search company or ticker
        </label>

        <div className="flex h-14 min-w-0 flex-1 items-center gap-3 rounded-xl border border-input bg-background px-4 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/25">
          <CompanySearch
            id={inputId}
            value={input}
            onValueChange={(value) => {
              setInput(value);
              setError(null);
            }}
            onSelect={(company) => add(company.ticker)}
            ariaLabel="Search company or ticker"
            placeholder="Search company or ticker (e.g. Microsoft or MSFT)"
            disabled={disabled || atLimit}
            inputClassName="h-full text-body"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          className="h-14 shrink-0 rounded-xl px-6"
          loading={isLoading}
          disabled={disabled || atLimit}
        >
          <Plus size={16} aria-hidden="true" />
          Add company
        </Button>
      </form>

      {error && (
        <p
          id={`${inputId}-error`}
          role="alert"
          className="mt-2.5 text-caption font-medium text-loss"
        >
          {error}
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span className="text-caption font-medium text-muted-foreground">
          Popular
        </span>

        {POPULAR_TICKERS.map((ticker) => {
          const selected = tickers.includes(ticker);

          return (
            <button
              key={ticker}
              type="button"
              onClick={() => add(ticker)}
              disabled={disabled || atLimit || selected}
              title={selected ? `${ticker} is already in the comparison` : `Add ${ticker}`}
              className={cn(
                "tnum inline-flex h-8 items-center gap-1.5 rounded-lg border px-2.5 font-mono text-caption font-semibold tracking-[0.04em] transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "border-border bg-surface text-muted-foreground",
                selected
                  ? "cursor-default opacity-45"
                  : "hover:border-border-strong hover:bg-muted hover:text-foreground",
                (disabled || atLimit) && !selected && "cursor-not-allowed opacity-55"
              )}
            >
              <CompanyLogo ticker={ticker} size="xs" decorative />

              {ticker}
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-4">
        <span className="text-caption font-medium text-muted-foreground">
          Selected
        </span>

        {tickers.map((ticker) => (
          <span
            key={ticker}
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-surface pl-2 pr-1.5"
          >
            <CompanyLogo ticker={ticker} size="xs" decorative />

            <span className="tnum font-mono text-caption font-semibold tracking-[0.05em] text-foreground">
              {ticker}
            </span>
            <button
              type="button"
              onClick={() => onRemove(ticker)}
              disabled={disabled}
              aria-label={`Remove ${ticker} from the comparison`}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-55"
            >
              <X size={13} aria-hidden="true" />
            </button>
          </span>
        ))}

        {tickers.length === 0 && (
          <p className="text-caption text-muted-foreground">
            No companies selected. Add at least two tickers.
          </p>
        )}
      </div>
    </section>
  );
}
