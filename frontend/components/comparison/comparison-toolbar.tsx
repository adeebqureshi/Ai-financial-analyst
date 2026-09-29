"use client";

import { Plus, Search, X } from "lucide-react";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { TickerBadge } from "@/components/ui/badge";
import { Field, TickerInput } from "@/components/ui/field";

type Props = {
  tickers: string[];
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
};

export function ComparisonToolbar({ tickers, onAdd, onRemove }: Props) {
  const inputId = useId();
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  function add() {
    const symbol = input.trim().toUpperCase();

    if (!symbol) {
      setError("Enter a ticker symbol to add.");
      return;
    }

    if (!/^[A-Z]{1,5}$/.test(symbol)) {
      setError("Ticker symbols are 1–5 letters (e.g. TSLA).");
      return;
    }

    setError(null);
    onAdd(symbol);
    setInput("");
  }

  return (
    <Card aria-labelledby="comparison-toolbar-heading">
      <CardHeader>
        <div>
          <CardTitle as="h2" id="comparison-toolbar-heading">
            Companies to compare
          </CardTitle>
          <p className="mt-1 text-label text-muted-foreground">
            Add two or more tickers. Every value is computed by the backend
            <code className="mx-1 rounded bg-muted px-1 font-mono text-caption text-foreground">
              /compare
            </code>
            endpoint.
          </p>
        </div>
      </CardHeader>

      <CardBody>
        <form
          className="flex flex-col gap-3 sm:flex-row sm:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            add();
          }}
        >
          <Field
            label="Add a ticker"
            htmlFor={inputId}
            error={error}
            className="flex-1"
          >
            <div className="flex h-10 items-center gap-2 rounded-lg border border-input bg-card px-3 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/25">
              <Search
                size={16}
                className="shrink-0 text-subtle-foreground"
                aria-hidden="true"
              />

              <TickerInput
                id={inputId}
                value={input}
                onValueChange={(value) => {
                  setInput(value);
                  setError(null);
                }}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? `${inputId}-error` : undefined}
                placeholder="TSLA"
                className="h-full border-0 bg-transparent px-0 focus-visible:border-0 focus-visible:ring-0"
              />
            </div>
          </Field>

          <Button type="submit">
            <Plus size={15} aria-hidden="true" />
            Add
          </Button>
        </form>

        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-4">
          {tickers.map((ticker) => (
            <span key={ticker} className="inline-flex items-center gap-1">
              <TickerBadge symbol={ticker} className="px-2 py-1" />
              <button
                type="button"
                onClick={() => onRemove(ticker)}
                aria-label={`Remove ${ticker} from the comparison`}
                className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X size={14} aria-hidden="true" />
              </button>
            </span>
          ))}

          {tickers.length === 0 && (
            <p className="text-label text-muted-foreground">
              No companies selected. Add at least two tickers.
            </p>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
