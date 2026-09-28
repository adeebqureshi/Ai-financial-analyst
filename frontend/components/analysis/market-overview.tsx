"use client";

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
import { SectionHeading } from "@/components/ui/page-header";
import type { MarketData, StatementData } from "@/types/analysis";

import { ChartFrame, ComparisonBars, RangePosition } from "./visuals";

type Props = { market: MarketData; statement: StatementData };

function isMissing(value: number | null | undefined): boolean {
  return value === null || value === undefined || Number.isNaN(value);
}

const MILLIONS = 1_000_000;

const NOT_PROVIDED = "Not provided by the market data provider";

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
    <div className="flex items-baseline justify-between gap-4 border-b border-border py-2.5 last:border-0">
      <dt className="text-label text-muted-foreground">{label}</dt>
      <dd className="tnum text-label font-medium text-foreground">{value}</dd>
    </div>
  );
}

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

  const incomeRows = [
    { label: "Revenue", value: statement.revenue },
    { label: "Operating income", value: statement.operating_income },
    { label: "Net income", value: statement.net_income },
    { label: "Free cash flow", value: statement.free_cash_flow },
  ];

  return (
    <section
      id="market"
      data-testid="market-overview"
      aria-labelledby="market-overview-heading"
      className="space-y-5 scroll-mt-32"
    >
      <SectionHeading
        id="market-overview-heading"
        title="Market overview"
        description="Latest quote plus the company's reported financial statements."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {market.stale && <Badge variant="warning">Quote may be stale</Badge>}

            {market.provider && (
              <span className="text-caption text-muted-foreground">
                Source: {market.provider}
                {quotesAsOf ? ` · ${quotesAsOf}` : ""}
              </span>
            )}
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {tiles.map((tile) => (
          <MetricCard key={tile.label} {...tile} />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <ChartFrame
          title="Reported income statement"
          description="Latest fiscal year, in USD"
          legend={
            <>
              <span className="inline-flex items-center gap-1.5">
                <span
                  className="size-2 rounded-full bg-chart-1"
                  aria-hidden="true"
                />
                Reported
              </span>
            </>
          }
          footer="Values are the backend&apos;s reported statement figures."
        >
          <ComparisonBars
            rows={incomeRows.map((row) => ({
              ...row,
              tone: row.value < 0 ? ("loss" as const) : ("brand" as const),
            }))}
            formatValue={(value) => formatCompactCurrency(dollars(value))}
          />
        </ChartFrame>

        <div className="space-y-4">
          <ChartFrame
            title="Price positioning"
            description="Where the quote sits in the reported range"
          >
            <RangePosition
              low={market.week_52_low}
              high={market.week_52_high}
              current={market.current_price}
              formatValue={(value) => formatCurrency(value)}
            />
          </ChartFrame>

          <div className="grid gap-4 sm:grid-cols-2">
            <ChartFrame title="Balance sheet" description="Reported, in USD">
              <dl>
                <StatementRow
                  label="Total assets"
                  value={formatCompactCurrency(dollars(statement.total_assets))}
                />
                <StatementRow
                  label="Total liabilities"
                  value={formatCompactCurrency(dollars(statement.total_liabilities))}
                />
                <StatementRow
                  label="Cash"
                  value={formatCompactCurrency(dollars(statement.cash))}
                />
                <StatementRow
                  label="Total debt"
                  value={formatCompactCurrency(dollars(statement.debt))}
                />
                <StatementRow
                  label="Shares outstanding"
                  value={formatShares(statement.shares_outstanding)}
                />
              </dl>
            </ChartFrame>

            <ChartFrame title="Cash generation" description="Reported, in USD">
              <dl>
                <StatementRow
                  label="Revenue"
                  value={formatCompactCurrency(dollars(statement.revenue))}
                />
                <StatementRow
                  label="Operating income"
                  value={formatCompactCurrency(dollars(statement.operating_income))}
                />
                <StatementRow
                  label="Net income"
                  value={formatCompactCurrency(dollars(statement.net_income))}
                />
                <StatementRow
                  label="Free cash flow"
                  value={formatCompactCurrency(dollars(statement.free_cash_flow))}
                />
              </dl>
            </ChartFrame>
          </div>
        </div>
      </div>
    </section>
  );
}
