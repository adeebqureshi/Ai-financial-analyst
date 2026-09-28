"use client";

import Link from "next/link";
import { ArrowUpRight, Star } from "lucide-react";

import { SectionHeading } from "@/components/ui/page-header";
import { TickerBadge } from "@/components/ui/badge";

type Shortcut = {
  symbol: string;
  company: string;
};

const shortcuts: Shortcut[] = [
  { symbol: "AAPL", company: "Apple" },
  { symbol: "MSFT", company: "Microsoft" },
  { symbol: "NVDA", company: "NVIDIA" },
  { symbol: "AMZN", company: "Amazon" },
  { symbol: "TSLA", company: "Tesla" },
  { symbol: "GOOGL", company: "Alphabet" },
];

export function Watchlist() {
  return (
    <section aria-labelledby="watchlist-heading" className="space-y-4">
      <SectionHeading
        id="watchlist-heading"
        title="Watchlist shortcuts"
        description="One click from a symbol to the full AI analysis. Prices are not streamed in this workspace — every symbol opens its live analysis."
        actions={
          <Link
            href="/watchlist"
            className="rounded-md text-caption font-medium text-brand underline-offset-4 transition-colors hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Open watchlist
          </Link>
        }
      />

      <ul className="grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 xl:grid-cols-3">
        {shortcuts.map((shortcut) => (
          <li key={shortcut.symbol} className="bg-card">
            <Link
              href={`/analysis/${shortcut.symbol}`}
              className="group flex items-center justify-between gap-3 px-4 py-3.5 transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
            >
              <span className="flex min-w-0 items-center gap-3">
                <Star
                  size={14}
                  className="shrink-0 text-border-strong transition-colors group-hover:text-brand"
                  aria-hidden="true"
                />
                <span className="min-w-0">
                  <TickerBadge symbol={shortcut.symbol} />
                  <span className="mt-1 block truncate text-caption text-muted-foreground">
                    {shortcut.company}
                  </span>
                </span>
              </span>

              <ArrowUpRight
                size={15}
                className="shrink-0 text-subtle-foreground transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand"
                aria-hidden="true"
              />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
