"use client";

import { useId, useState } from "react";

import { Button } from "./button";
import { Field, TickerInput } from "./field";

type Props = {

  submitLabel?: string;

  hint?: string;
  onSubmit: (symbol: string) => void;
  className?: string;
};

const SYMBOL_PATTERN = /^[A-Z]{1,5}$/;


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
