"use client";

import {
  Activity,
  BarChart3,
  Building2,
  DollarSign,
  Globe,
  Landmark,
  LineChart,
  Percent,
  TrendingUp,
  Wallet,
} from "lucide-react";

import type {
  MarketData,
  StatementData,
} from "@/types/analysis";

type Props = {
  market: MarketData;
  statement: StatementData;
};

function formatCompact(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  const abs = Math.abs(value);
  if (abs >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
  return `$${value.toLocaleString()}`;
}

function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `$${value.toFixed(2)}`;
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function MetricCard({
  title,
  value,
  subtitle,
  color,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl transition-all duration-300 hover:border-blue-500/30 hover:bg-white/[0.05]">

      <div className={`inline-flex rounded-2xl p-3 ${color}`}>
        {icon}
      </div>

      <p className="mt-5 text-sm text-zinc-500">
        {title}
      </p>

      <h2 className="mt-3 text-3xl font-bold text-white">
        {value}
      </h2>

      <p className="mt-3 text-sm text-zinc-500">
        {subtitle}
      </p>

    </div>
  );
}

function StatementRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 py-4 last:border-0">

      <p className="text-zinc-400">
        {label}
      </p>

      <p className="font-semibold text-white">
        {value}
      </p>

    </div>
  );
}

// Backend statement figures are expressed in $M (millions); convert to raw
// dollars for display.
const statementDollars = (value: number): number =>
  value * 1_000_000;

export function MarketOverview({
  market,
  statement,
}: Props) {
  return (
    <section>

      <div className="mb-8">

        <h2 className="text-3xl font-bold text-white">
          Market Overview
        </h2>

        <p className="mt-2 text-zinc-500">
          Live market snapshot and financial statement
        </p>

      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

        <MetricCard
          title="Current Price"
          value={formatPrice(market.current_price)}
          subtitle={market.exchange ?? "Market"}
          color="bg-emerald-500/10"
          icon={
            <DollarSign
              size={22}
              className="text-emerald-400"
            />
          }
        />

        <MetricCard
          title="Market Cap"
          value={formatCompact(market.market_cap)}
          subtitle={market.currency}
          color="bg-blue-500/10"
          icon={
            <Building2
              size={22}
              className="text-blue-400"
            />
          }
        />

        <MetricCard
          title="P/E Ratio"
          value={
            market.pe_ratio === null ||
            market.pe_ratio === undefined
              ? "—"
              : market.pe_ratio.toFixed(2)
          }
          subtitle="Trailing"
          color="bg-violet-500/10"
          icon={
            <TrendingUp
              size={22}
              className="text-violet-400"
            />
          }
        />

        <MetricCard
          title="Beta"
          value={
            market.beta === null ||
            market.beta === undefined
              ? "—"
              : market.beta.toFixed(2)
          }
          subtitle="Volatility vs. market"
          color="bg-orange-500/10"
          icon={
            <Activity
              size={22}
              className="text-orange-400"
            />
          }
        />

        <MetricCard
          title="EPS"
          value={formatPrice(market.eps)}
          subtitle="Trailing earnings per share"
          color="bg-cyan-500/10"
          icon={
            <LineChart
              size={22}
              className="text-cyan-400"
            />
          }
        />

        <MetricCard
          title="Dividend Yield"
          value={formatPercent(market.dividend_yield)}
          subtitle="Annual yield"
          color="bg-amber-500/10"
          icon={
            <Percent
              size={22}
              className="text-amber-400"
            />
          }
        />

        <MetricCard
          title="52-Week Range"
          value={`${formatPrice(market.week_52_low)} – ${formatPrice(market.week_52_high)}`}
          subtitle="Low – high"
          color="bg-rose-500/10"
          icon={
            <BarChart3
              size={22}
              className="text-rose-400"
            />
          }
        />

        <MetricCard
          title="Volume"
          value={
            market.volume === null ||
            market.volume === undefined
              ? "—"
              : market.volume.toLocaleString()
          }
          subtitle="Trading volume"
          color="bg-teal-500/10"
          icon={
            <Globe
              size={22}
              className="text-teal-400"
            />
          }
        />

      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">

        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">

          <div className="mb-4 flex items-center gap-3">

            <Landmark
              size={20}
              className="text-blue-400"
            />

            <h3 className="text-xl font-semibold text-white">
              Balance Sheet
            </h3>

          </div>

          <StatementRow
            label="Total Assets"
            value={formatCompact(statementDollars(statement.total_assets))}
          />

          <StatementRow
            label="Total Liabilities"
            value={formatCompact(statementDollars(statement.total_liabilities))}
          />

          <StatementRow
            label="Cash"
            value={formatCompact(statementDollars(statement.cash))}
          />

          <StatementRow
            label="Total Debt"
            value={formatCompact(statementDollars(statement.debt))}
          />

          <StatementRow
            label="Shares Outstanding"
            value={
              statement.shares_outstanding
                ? `${(statement.shares_outstanding / 1000).toFixed(1)}B`
                : "—"
            }
          />

        </div>

        <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">

          <div className="mb-4 flex items-center gap-3">

            <Wallet
              size={20}
              className="text-emerald-400"
            />

            <h3 className="text-xl font-semibold text-white">
              Income Statement
            </h3>

          </div>

          <StatementRow
            label="Revenue"
            value={formatCompact(statementDollars(statement.revenue))}
          />

          <StatementRow
            label="Operating Income"
            value={formatCompact(statementDollars(statement.operating_income))}
          />

          <StatementRow
            label="Net Income"
            value={formatCompact(statementDollars(statement.net_income))}
          />

          <StatementRow
            label="Free Cash Flow"
            value={formatCompact(statementDollars(statement.free_cash_flow))}
          />

        </div>

      </div>

    </section>
  );
}
