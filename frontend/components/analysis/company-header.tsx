"use client";

import { Activity, Building2, Landmark, Sparkles } from "lucide-react";

import { Badge, DemoBadge, RecommendationBadge, TickerBadge } from "@/components/ui/badge";
import { Delta, formatCurrency, formatPercent } from "@/components/ui/metric";
import { cn } from "@/lib/utils";

type Props = {
  company: {
    name: string;
    ticker: string;
    sector?: string;
    industry?: string;
    description?: string;
  };

  recommendation: string;

  price?: number | null;
  upside?: number | null;
  intrinsicValue?: number | null;
  stale?: boolean;
  asOf?: string | null;
};

function isDemoData(name: string): boolean {
  return name.includes("[DEMO / SYNTHETIC DATA]");
}

function formatAsOf(value: string | null | undefined): string | null {
  if (!value) return null;

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toLocaleString();
}

export function CompanyHeader({
  company,
  recommendation,
  price,
  upside,
  intrinsicValue,
  stale,
  asOf,
}: Props) {
  const isDemo = isDemoData(company.name);
  const displayName = isDemo
    ? company.name.replace(" [DEMO / SYNTHETIC DATA]", "")
    : company.name;

  const asOfLabel = formatAsOf(asOf);
  const hasQuote = typeof price === "number" && !Number.isNaN(price);

  return (
    <section
      data-testid="company-header"
      aria-labelledby="company-heading"
      className="border-b border-border pb-8"
    >
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="brand">
              <Activity size={13} aria-hidden="true" />
              AI Analysis
            </Badge>

            <Badge variant="outline">
              <Sparkles size={13} aria-hidden="true" />
              Live pipeline
            </Badge>

            {isDemo && <DemoBadge label="Demo data" />}
            {stale && <Badge variant="warning">Quote may be stale</Badge>}
          </div>

          <h1
            id="company-heading"
            data-testid="company-name"
            className="mt-4 text-balance text-display text-foreground"
          >
            {displayName}
          </h1>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <TickerBadge symbol={company.ticker} className="px-2 py-1 text-body" />

            {company.sector && (
              <Badge variant="neutral">
                <Landmark size={13} aria-hidden="true" />
                {company.sector}
              </Badge>
            )}

            {company.industry && (
              <Badge variant="neutral">
                <Building2 size={13} aria-hidden="true" />
                {company.industry}
              </Badge>
            )}
          </div>

          {company.description && (
            <p className="mt-5 max-w-3xl text-body leading-relaxed text-muted-foreground">
              {company.description}
            </p>
          )}

          {isDemo && (
            <p className="mt-4 rounded-lg border border-warning/25 bg-warning-subtle px-3.5 py-2.5 text-caption text-warning">
              All values shown for this company come from the backend&apos;s
              synthetic demo fixtures, not from live market data.
            </p>
          )}
        </div>

        <aside
          className="rounded-xl border border-border bg-card p-5 shadow-card xl:sticky xl:top-24"
          aria-label="Quote and recommendation"
        >
          <p className="text-caption font-semibold uppercase tracking-[0.1em] text-subtle-foreground">
            Latest quote
          </p>

          <div className="mt-2 flex flex-wrap items-baseline gap-3">
            <span
              className={cn(
                "tnum text-display",
                hasQuote ? "text-foreground" : "text-subtle-foreground"
              )}
            >
              {hasQuote ? formatCurrency(price as number) : "—"}
            </span>

            {typeof upside === "number" && !Number.isNaN(upside) && (
              <Delta value={upside} />
            )}
          </div>

          {asOfLabel && (
            <p className="mt-1.5 text-caption text-muted-foreground">
              As of {asOfLabel}
            </p>
          )}

          <div className="mt-4 space-y-2.5 border-t border-border pt-4">
            <div className="flex items-center justify-between gap-3">
              <span className="text-label text-muted-foreground">
                Backend recommendation
              </span>
              <RecommendationBadge recommendation={recommendation} />
            </div>

            {typeof intrinsicValue === "number" &&
              !Number.isNaN(intrinsicValue) && (
                <div className="flex items-center justify-between gap-3">
                  <span className="text-label text-muted-foreground">
                    Intrinsic value
                  </span>
                  <span className="tnum text-label font-medium text-foreground">
                    {formatCurrency(intrinsicValue)}
                  </span>
                </div>
              )}

            {typeof upside === "number" && !Number.isNaN(upside) && (
              <div className="flex items-center justify-between gap-3">
                <span className="text-label text-muted-foreground">Upside</span>
                <span className="tnum text-label font-medium text-foreground">
                  {formatPercent(upside)}
                </span>
              </div>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
