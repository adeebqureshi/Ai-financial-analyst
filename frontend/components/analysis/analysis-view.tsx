"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/services/api";
import { useAnalysis } from "@/hooks/use-analysis";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonAnalysisView } from "@/components/ui/skeleton";

import { CompanyHeader } from "./company-header";
import { ExecutiveSummary } from "./executive-summary";
import { ValuationCards } from "./valuation-cards";
import { FinancialHealth } from "./financial-health";
import { RiskAnalysis } from "./risk-analysis";
import { MarketOverview } from "./market-overview";
import { AIChat } from "./ai-chat";

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

  const result =
    (query.data as ApiResponse<AnalyzeData> | undefined)?.data ?? null;

  const health = result?.health ?? null;

  /**
   * Real risk assessment from `POST /risk-analysis`, requested with the
   * health scores returned by `/analyze`. Only runs once those scores exist;
   * the endpoint does not provide volatility or business/financial risk
   * percentages, so none are displayed.
   */
  const riskQuery = useQuery({
    queryKey: [
      "risk-analysis",
      ticker,
      health?.piotroski_score,
      health?.altman_score,
      health?.beneish_score,
    ],
    queryFn: () =>
      api.riskAnalysis({
        piotroski_score: health!.piotroski_score,
        altman_score: health!.altman_score,
        beneish_score: health!.beneish_score,
      }),
    enabled: Boolean(health),
    retry: false,
  });

  if (query.isPending) {
    return <SkeletonAnalysisView />;
  }

  if (query.isError) {
    return (
      <ErrorDisplay
        error={query.error}
        onRetry={() => query.refetch()}
        title="Analysis Failed"
      />
    );
  }

  if (!result) {
    return (
      <ErrorDisplay
        error={new Error("No analysis data was returned for this ticker.")}
        title="Analysis Failed"
      />
    );
  }

  const recommendation =
    result.recommendation;

  const valuation =
    result.valuation;

  const market =
    result.market;

  const statement =
    result.statement;

  const company = {
    name: result.company.name,
    ticker: result.company.ticker,
    sector: result.company.sector ?? undefined,
    industry: result.company.industry ?? undefined,
    description: result.company.description ?? undefined,
  };

  return (

    <div className="space-y-10">

      <CompanyHeader
        company={company}
        recommendation={recommendation}
      />

      <ExecutiveSummary
        recommendation={recommendation}
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
        score={health!.score}
        rating={health!.rating}
        piotroski={
          health!.piotroski_score
        }
        altman={
          health!.altman_score
        }
        beneish={
          health!.beneish_score
        }
      />

      <RiskAnalysis
        beta={market.beta ?? null}
        risk={riskQuery.data?.data ?? null}
        isLoading={riskQuery.isPending}
        isError={riskQuery.isError}
        onRetry={() => riskQuery.refetch()}
      />

      <AIChat ticker={ticker} />

    </div>

  );
}
