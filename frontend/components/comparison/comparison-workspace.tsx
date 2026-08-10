"use client";

import { useState } from "react";

import { ComparisonToolbar } from "./comparison-toolbar";
import { ComparisonTable } from "./comparison-table";

const defaults = [
  "AAPL",
  "MSFT",
  "NVDA",
  "GOOGL",
];

export function ComparisonWorkspace() {
  const [tickers, setTickers] =
    useState<string[]>(defaults);

  function addTicker(ticker: string) {
    const symbol = ticker.trim().toUpperCase();

    if (
      !symbol ||
      !/^[A-Z]{1,5}$/.test(symbol) ||
      tickers.includes(symbol)
    ) {
      return;
    }

    setTickers((prev) => [...prev, symbol]);
  }

  function removeTicker(ticker: string) {
    setTickers((prev) =>
      prev.filter((t) => t !== ticker)
    );
  }

  return (
    <div className="space-y-10">

      <ComparisonToolbar
        tickers={tickers}
        onAdd={addTicker}
        onRemove={removeTicker}
      />

      <ComparisonTable
        tickers={tickers}
      />

    </div>
  );
}
