"use client";

import { useId, useState } from "react";
import { ArrowRight } from "lucide-react";

import { Button } from "./button";
import { Field, TickerInput } from "./field";

type Props = {
  /** Label of the submit button. */
  submitLabel?: string;
  /** Helper text rendered under the field. */
  hint?: string;
  onSubmit: (symbol: string) => void;
  className?: string;
};

const SYMBOL_PATTERN = /^[A-Z]{1,5}$/;

/**
 * Ticker entry used by the `/analysis` and `/company` landing pages.
 *
 * Extracted so both routes render the same validated control instead of two
 * near-identical local forms. Validation mirrors the backend contract
 * (1–5 uppercase letters) and is announced through `aria-describedby`/`role`.
 */
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

        <Button onClick={submit} disabled={!valid} className="sm:mb-0">
          {submitLabel}
          <ArrowRight className="size-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
