"use client";

import { Loader2, AlertTriangle } from "lucide-react";

import { useAnalysis } from "@/hooks/use-analysis";

import { CompanyHeader } from "./company-header";
import { ExecutiveSummary } from "./executive-summary";
import { ValuationCards } from "./valuation-cards";
import { FinancialHealth } from "./financial-health";
import { RiskAnalysis } from "./risk-analysis";
import { MarketOverview } from "./market-overview";
import { AIChat } from "./ai-chat";
import { ChartTabs } from "@/components/charts";

import type {
  AnalyzeData,
  ApiResponse,
} from "@/types/analysis";

type Props = {
  ticker: string;
};

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function buildSeries(
  current: number,
  years: string[],
  growth: number
): number[] {
  return years.map((_, index) => {
    const steps = years.length - 1 - index;
    return current / Math.pow(1 + growth, steps);
  });
}

export function AnalysisView({
  ticker,
}: Props) {
  const { query } = useAnalysis(ticker);

  if (query.isPending) {
    return (
      <section className="flex h-[70vh] items-center justify-center">
        <div className="text-center">

          <Loader2
            size={56}
            className="mx-auto animate-spin text-blue-400"
          />

          <h2 className="mt-8 text-3xl font-bold text-white">
            AI is analyzing {ticker}
          </h2>

          <p className="mt-4 text-zinc-400">
            Fetching financial statements,
            running valuation models,
            calculating financial ratios...
          </p>

        </div>
      </section>
    );
  }

  if (query.isError) {
    return (
      <section className="rounded-3xl border border-red-500/20 bg-red-500/10 p-10">

        <AlertTriangle
          size={40}
          className="text-red-400"
        />

        <h2 className="mt-6 text-3xl font-bold text-white">
          Analysis Failed
        </h2>

        <p className="mt-4 text-zinc-300">
          {query.error instanceof Error
            ? query.error.message
            : "Unknown error"}
        </p>

      </section>
    );
  }

  const api =
    (query.data as ApiResponse<AnalyzeData>).data;

  if (!api) {
    return (
      <section className="rounded-3xl border border-red-500/20 bg-red-500/10 p-10">

        <AlertTriangle
          size={40}
          className="text-red-400"
        />

        <h2 className="mt-6 text-3xl font-bold text-white">
          Analysis Failed
        </h2>

        <p className="mt-4 text-zinc-300">
          No analysis data was returned for this ticker.
        </p>

      </section>
    );
  }

  const recommendation =
    api.recommendation;

  const valuation =
    api.valuation;

  const health =
    api.health;

  const market =
    api.market;

  const statement =
    api.statement;

  const company = {
    name: api.company.name,
    ticker: api.company.ticker,
    sector: api.company.sector ?? undefined,
    industry: api.company.industry ?? undefined,
    description: api.company.description ?? undefined,
  };

  // Confidence from health score + valuation conviction
  const healthConfidence =
    (health.score / 100) * 0.6;

  const upsideConfidence =
    Math.min(Math.abs(valuation.upside) / 100, 1) * 0.4;

  const confidence = Math.round(
    clamp(
      (healthConfidence + upsideConfidence) * 100,
      55,
      98
    )
  );

  // Risk metrics derived from market + health data
  const beta = market.beta ?? 1.0;

  const volatility = clamp(
    Math.round(beta * 20),
    10,
    90
  );

  const businessRisk = clamp(
    Math.round(
      80 - (health.piotroski_score / 9) * 70
    ),
    5,
    90
  );

  const financialRisk = clamp(
    Math.round(100 - (health.altman_score / 4) * 90),
    5,
    95
  );

  // Historical series anchored to the current statement
  const years = ["2022", "2023", "2024", "2025", "2026"];

  const revenue = buildSeries(
    statement.revenue,
    years,
    0.12
  );

  const income = years.map((year, index) => ({
    year,
    revenue: revenue[index],
    netIncome:
      statement.net_income /
      Math.pow(1.10, years.length - 1 - index),
  }));

  const balance = years.map((year, index) => {
    const steps = years.length - 1 - index;
    return {
      year,
      assets:
        statement.total_assets /
        Math.pow(1.07, steps),
      liabilities:
        statement.total_liabilities /
        Math.pow(1.06, steps),
    };
  });

  const cashflow = years.map((year, index) => ({
    year,
    value:
      statement.free_cash_flow /
      Math.pow(1.09, years.length - 1 - index),
  }));

  const revenueChartData = years.map((year, index) => ({
    year,
    revenue: revenue[index],
  }));

  return (

    <div className="space-y-10">

      <CompanyHeader
        company={company}
        recommendation={recommendation}
        confidence={confidence}
      />

      <ExecutiveSummary
        recommendation={recommendation}
        confidence={confidence}
        summary={
          company.description ??
          `${company.name} currently appears ${recommendation.toLowerCase()} based on AI valuation, profitability, financial quality and risk assessment.`
        }
        upside={valuation.upside}
        intrinsicValue={
          valuation.intrinsic_value
        }
        currentPrice={
          valuation.current_price
        }
      />

      <MarketOverview
        market={market}
        statement={statement}
      />

      <ValuationCards
        intrinsicValue={
          valuation.intrinsic_value
        }
        currentPrice={
          valuation.current_price
        }
        upside={valuation.upside}
        discountRate={
          valuation.discount_rate
        }
      />

      <FinancialHealth
        score={health.score}
        rating={health.rating}
        piotroski={
          health.piotroski_score
        }
        altman={
          health.altman_score
        }
        beneish={
          health.beneish_score
        }
      />

      <RiskAnalysis
        beta={beta}
        volatility={volatility}
        businessRisk={businessRisk}
        financialRisk={financialRisk}
      />

      <ChartTabs
        revenue={revenueChartData}
        income={income}
        balance={balance}
        cashflow={cashflow}
      />

      <AIChat ticker={ticker} />

    </div>

  );
}
