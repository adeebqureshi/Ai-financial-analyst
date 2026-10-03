"use client";

import { useId, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

import { CompanyLogo } from "@/components/company/company-logo";
import { cn } from "@/lib/utils";

import { Button } from "./button";
import { Field, TickerInput } from "./field";

type Props = {

  submitLabel?: string;

  hint?: string;
  onSubmit: (symbol: string) => void;
  className?: string;
};

const SYMBOL_PATTERN = /^[A-Z]{1,5}$/;

/**
 * Broadly covered US large caps. Symbols only — identity, company names and
 * logos are resolved centrally by `@/lib/company-logos`, so this list is never
 * the place to add logo data.
 */
export const POPULAR_TICKERS = [
  "AAPL",
  "MSFT",
  "NVDA",
  "AMZN",
  "GOOGL",
  "TSLA",
] as const;

/**
 * Examples disclosure — a popover of popular symbols that writes the chosen
 * symbol into the page's ticker field.
 *
 * A convenience shortcut only, never the sole way to enter a ticker, so it
 * collapses away on small screens where the popular chips serve the same role.
 * Shared by Analyze and Company so both pages look and behave identically.
 */
export function TickerExamplesMenu({
  onSelect,
  className,
}: {
  onSelect: (symbol: string) => void;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  return (
    <div ref={wrapperRef} className={cn("relative shrink-0", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="true"
        aria-controls={menuId}
        onClick={() => setOpen((value) => !value)}
        onBlur={(event) => {
          if (!wrapperRef.current?.contains(event.relatedTarget)) {
            setOpen(false);
          }
        }}
        className={cn(
          "inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-surface px-3 text-label font-medium text-foreground",
          "transition-colors hover:border-border-strong hover:bg-muted",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        )}
      >
        Examples
        <ChevronDown
          size={14}
          aria-hidden="true"
          className={cn(
            "text-subtle-foreground transition-transform duration-150",
            open && "rotate-180"
          )}
        />
      </button>

      {open && (
        <ul
          id={menuId}
          className="absolute right-0 top-full z-20 mt-1.5 grid w-56 grid-cols-2 gap-1 rounded-xl border border-border bg-popover p-1.5 shadow-overlay"
        >
          {POPULAR_TICKERS.map((symbol) => (
            <li key={symbol}>
              <button
                type="button"
                onClick={() => {
                  onSelect(symbol);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-left transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <CompanyLogo ticker={symbol} size="xs" decorative />

                <span className="tnum font-mono text-caption font-medium text-foreground">
                  {symbol}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}


export function TickerLookupForm({
  submitLabel = "Continue",
  hint,
  onSubmit,
  className,
}: Props) {
  const inputId = useId();
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState<string | null>(null);

  const symbol = ticker.trim().toUpperCase();
  const valid = SYMBOL_PATTERN.test(symbol);

  function submit() {
    if (!SYMBOL_PATTERN.test(symbol)) {
      setError(
        symbol.length === 0
          ? "Enter a ticker symbol."
          : "Ticker symbols are 1–5 letters (e.g. AAPL)."
      );
      return;
    }

    setError(null);
    onSubmit(symbol);
  }

  return (
    <div className={className}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <Field
          label="Ticker symbol"
          htmlFor={inputId}
          hint={hint}
          error={error}
          required
          className="sm:max-w-40"
        >
          <TickerInput
            id={inputId}
            value={ticker}
            onValueChange={(value) => {
              setTicker(value);
              setError(null);
            }}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? `${inputId}-error` : undefined}
            placeholder="AAPL"
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                submit();
              }
            }}
          />
        </Field>

        {/* Lookups are a short, repeatable step rather than the page's
            headline CTA, so the submit stays a compact secondary control. */}
        <Button
          onClick={submit}
          disabled={!valid}
          variant="secondary"
          size="md"
          className="sm:mb-0"
        >
          {submitLabel}
        </Button>
      </div>
    </div>
  );
}
