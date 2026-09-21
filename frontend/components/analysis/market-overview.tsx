"use client";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  EMPTY_VALUE,
  MetricCard,
  formatCompactCurrency,
  formatCurrency,
  formatNumber,
  formatRatio,
  formatRatioAsPercent,
} from "@/components/ui/metric";
import type { MarketData, StatementData } from "@/types/analysis";

type Props = { market: MarketData; statement: StatementData };

function isMissing(value: number | null | undefined): boolean {
  return value === null || value === undefined || Number.isNaN(value);
}

/** Backend statement figures are reported in millions of USD. */
const MILLIONS = 1_000_000;

const NOT_PROVIDED = "Not provided by the market data provider";

/** Backend `shares_outstanding` is in millions. */
function formatShares(value: number | null | undefined): string {
  if (isMissing(value)) return EMPTY_VALUE;
  return `${((value as number) / 1000).toFixed(1)}B`;
}

function quoteTimestamp(asOf: string | null | undefined): string | null {
  if (!asOf) return null;
  const parsed = new Date(asOf);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toLocaleString();
}

function StatementRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border py-2.5 last:border-0">
      <dt className="text-label text-muted-foreground">{label}</dt>
      <dd className="tnum text-label font-medium text-foreground">{value}</dd>
    </div>
  );
}

/**
 * Market snapshot and statements, straight from the `/analyze` payload.
 *
 * Values the provider did not supply render an explicit "not provided" state
 * rather than a zero; statement figures ($M) are converted to dollars.
 */
export function MarketOverview({ market, statement }: Props) {
  const quoteAvailable = !isMissing(market.current_price);
  const quotesAsOf = quoteTimestamp(market.as_of);
  const dollars = (value: number) => value * MILLIONS;
  const rangeMissing =
    isMissing(market.week_52_low) || isMissing(market.week_52_high);

  const tiles = [
    {
      label: "Current price",
      value: formatCurrency(market.current_price),
      hint: quoteAvailable ? market.exchange ?? market.currency : NOT_PROVIDED,
    },
    {
      label: "Market cap",
      value: formatCompactCurrency(market.market_cap),
      hint: isMissing(market.market_cap) ? NOT_PROVIDED : market.currency,
    },
    {
      label: "P/E ratio",
      value: formatRatio(market.pe_ratio),
      hint: isMissing(market.pe_ratio) ? NOT_PROVIDED : "Trailing",
    },
    {
      label: "Beta",
      value: formatRatio(market.beta),
      hint: isMissing(market.beta) ? NOT_PROVIDED : "Market sensitivity",
    },
    {
      label: "EPS",
      value: formatCurrency(market.eps),
      hint: isMissing(market.eps) ? NOT_PROVIDED : "Trailing EPS",
    },
    {
      label: "Dividend yield",
      value: formatRatioAsPercent(market.dividend_yield),
      hint: isMissing(market.dividend_yield) ? NOT_PROVIDED : "Annual yield",
    },
    {
      label: "52-week range",
      value: rangeMissing
        ? EMPTY_VALUE
        : `${formatCurrency(market.week_52_low)} – ${formatCurrency(
            market.week_52_high
          )}`,
      hint: rangeMissing ? NOT_PROVIDED : "Low – high",
    },
    {
      label: "Volume",
      value: formatNumber(market.volume),
      hint: isMissing(market.volume) ? NOT_PROVIDED : "Latest session",
    },
  ];

  return (
    <section
      data-testid="market-overview"
      aria-labelledby="market-overview-heading"
    >
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="market-overview-heading" className="text-title text-foreground">
            Market overview
          </h2>
          <p className="mt-1 text-label text-muted-foreground">
            Latest quote and the company&apos;s reported financial statements.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {market.stale && <Badge variant="warning">Quote may be stale</Badge>}

          {market.provider && (
            <span className="text-caption text-subtle-foreground">
              Source: {market.provider}
              {quotesAsOf ? ` · ${quotesAsOf}` : ""}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {tiles.map((tile) => (
          <MetricCard key={tile.label} {...tile} />
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {[
          {
            title: "Balance sheet",
            rows: [
              ["Total assets", statement.total_assets],
              ["Total liabilities", statement.total_liabilities],
              ["Cash", statement.cash],
              ["Total debt", statement.debt],
            ] as const,
            extra: (
              <StatementRow
                label="Shares outstanding"
                value={formatShares(statement.shares_outstanding)}
              />
            ),
          },
          {
            title: "Income statement",
            rows: [
              ["Revenue", statement.revenue],
              ["Operating income", statement.operating_income],
              ["Net income", statement.net_income],
              ["Free cash flow", statement.free_cash_flow],
            ] as const,
            extra: null,
          },
        ].map((section) => (
          <Card key={section.title}>
            <CardHeader>
              <CardTitle as="h3">{section.title}</CardTitle>
              <span className="text-caption text-subtle-foreground">
                Reported, in USD
              </span>
            </CardHeader>

            <CardBody>
              <dl>
                {section.rows.map(([label, value]) => (
                  <StatementRow
                    key={label}
                    label={label}
                    value={formatCompactCurrency(dollars(value))}
                  />
                ))}
                {section.extra}
              </dl>
            </CardBody>
          </Card>
        ))}
      </div>
    </section>
  );
}
