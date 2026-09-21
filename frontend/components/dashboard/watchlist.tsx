"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";

type Shortcut = {
  symbol: string;
  company: string;
};

/**
 * Navigation shortcuts only — no prices or changes are shown because no
 * dashboard endpoint provides them. Live values appear on each company's
 * analysis page, sourced from the backend.
 */
const shortcuts: Shortcut[] = [
  { symbol: "AAPL", company: "Apple" },
  { symbol: "MSFT", company: "Microsoft" },
  { symbol: "NVDA", company: "NVIDIA" },
  { symbol: "AMZN", company: "Amazon" },
  { symbol: "TSLA", company: "Tesla" },
];

export function Watchlist() {
  return (
    <Card aria-labelledby="shortcuts-heading">
      <CardHeader>
        <div>
          <CardTitle as="h2" id="shortcuts-heading">
            Shortcuts
          </CardTitle>
          <p className="mt-1 text-label text-muted-foreground">
            Quick links to AI analysis for frequently researched companies.
          </p>
        </div>
      </CardHeader>

      <CardBody>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {shortcuts.map((shortcut) => (
            <Link
              key={shortcut.symbol}
              href={`/analysis/${shortcut.symbol}`}
              className="group flex items-center justify-between gap-3 rounded-lg border border-border bg-background px-4 py-3 transition-colors hover:border-border-strong hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <span className="min-w-0">
                <span className="block font-mono text-label font-semibold text-foreground">
                  {shortcut.symbol}
                </span>
                <span className="block truncate text-caption text-muted-foreground">
                  {shortcut.company}
                </span>
              </span>

              <ArrowUpRight
                className="size-4 shrink-0 text-muted-foreground transition group-hover:text-foreground"
                aria-hidden="true"
              />
            </Link>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
