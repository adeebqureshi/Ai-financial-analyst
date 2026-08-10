"use client";

import { Loader2, AlertTriangle } from "lucide-react";

import { useAnalysis } from "@/hooks/use-analysis";

import { CompanyHeader } from "./company-header";
import { ExecutiveSummary } from "./executive-summary";
import { ValuationCards } from "./valuation-cards";
import { FinancialHealth } from "./financial-health";
import { RiskAnalysis } from "./risk-analysis";
import { MarketOverview } from "./market-overview";
import {
  RevenueChart,
  CashFlowChart,
} from "@/components/charts";

import type {
  AnalyzeData,
  ApiResponse,
} from "@/types/analysis";

type Props = {
  ticker: string;
};

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

  const company = {
    name: api.company.name,
    ticker: api.company.ticker,
    sector: api.company.sector ?? undefined,
    industry: api.company.industry ?? undefined,
    description: api.company.description ?? undefined,
  };

  return (

    <div className="space-y-10">

      <CompanyHeader
        company={company}
        recommendation={recommendation}
        confidence={92}
      />

      <ExecutiveSummary
        recommendation={recommendation}
        confidence={92}
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
        market={api.market}
        statement={api.statement}
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

      <RiskAnalysis />

      <div className="grid gap-8 xl:grid-cols-2">

        <RevenueChart
          revenue={[
            260,
            274,
            294,
            318,
            341,
          ]}
        />

        <CashFlowChart
          cashflow={[
            74,
            81,
            92,
            101,
            108,
          ]}
        />

      </div>

    </div>

  );
}