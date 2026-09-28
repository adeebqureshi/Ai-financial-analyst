"use client";

import Link from "next/link";
import { ArrowUpRight, Eye } from "lucide-react";

import { SectionHeading } from "@/components/ui/page-header";
import { TickerBadge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";

const tracked = [
  { symbol: "AAPL", company: "Apple" },
  { symbol: "MSFT", company: "Microsoft" },
  { symbol: "NVDA", company: "NVIDIA" },
  { symbol: "AMZN", company: "Amazon" },
  { symbol: "TSLA", company: "Tesla" },
];

export default function WatchlistPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-8">
      <div className="flex flex-col gap-4 border-b border-border pb-7 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-caption font-semibold uppercase tracking-[0.16em] text-brand">
            Workspace
          </p>
          <h1 className="mt-2 text-display text-foreground">Watchlist</h1>
          <p className="mt-2.5 max-w-2xl text-body text-muted-foreground">
            Companies you follow. Prices and changes appear once a market data
            feed is connected to this workspace — until then, each symbol links
            straight to its live analysis.
          </p>
        </div>

        <Button asChild variant="secondary" size="sm">
          <Link href="/analysis">
            Add a symbol
            <ArrowUpRight size={15} aria-hidden="true" />
          </Link>
        </Button>
      </div>

      <EmptyState
        icon={<Eye size={20} aria-hidden="true" />}
        title="Your watchlist is empty"
        description="This workspace does not persist a watchlist yet. Use the symbols below as research shortcuts — each one opens the full analysis workspace."
      />

      <section aria-labelledby="tracked-symbols" className="space-y-4">
        <SectionHeading
          id="tracked-symbols"
          title="Research shortcuts"
          description="Frequently followed companies in this workspace."
        />

        <ul className="grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 xl:grid-cols-3">
          {tracked.map((item) => (
            <li key={item.symbol} className="bg-card">
              <Link
                href={`/analysis/${item.symbol}`}
                className="group flex items-center justify-between gap-3 px-4 py-3.5 transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <TickerBadge symbol={item.symbol} className="px-2 py-1" />
                  <span className="truncate text-caption text-muted-foreground">
                    {item.company}
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
    </div>
  );
}
