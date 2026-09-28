"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/services/api";
import { useAnalysis } from "@/hooks/use-analysis";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonAnalysisView } from "@/components/ui/skeleton";
import { SectionHeading } from "@/components/ui/page-header";

import { AnalysisSectionNav } from "./section-nav";
import { CompanyHeader } from "./company-header";
import { ExecutiveSummary } from "./executive-summary";
import { ValuationCards } from "./valuation-cards";
import { FinancialHealth } from "./financial-health";
import { RiskAnalysis } from "./risk-analysis";
import { MarketOverview } from "./market-overview";
import { AIChat } from "./ai-chat";

import type { AnalyzeData, ApiResponse } from "@/types/analysis";

type Props = {
  ticker: string;
};

const SECTIONS = [
  { id: "summary", label: "Summary" },
  { id: "market", label: "Market" },
  { id: "valuation", label: "Valuation" },
  { id: "health", label: "Health" },
  { id: "risk", label: "Risk" },
  { id: "insights", label: "AI Insights" },
];

export function AnalysisView({ ticker }: Props) {
  const { query } = useAnalysis(ticker);

  const result =
    (query.data as ApiResponse<AnalyzeData> | undefined)?.data ?? null;

  const health = result?.health ?? null;

  const sections = useMemo(() => SECTIONS, []);

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

  const recommendation = result.recommendation;

  const valuation = result.valuation;

  const market = result.market;

  const statement = result.statement;

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
        price={market.current_price}
        upside={valuation.upside}
        intrinsicValue={valuation.intrinsic_value}
        stale={market.stale}
        asOf={market.as_of}
      />

      <AnalysisSectionNav sections={sections} />

      <ExecutiveSummary
        recommendation={recommendation}
        summary={null}
        upside={valuation.upside}
        intrinsicValue={valuation.intrinsic_value}
        currentPrice={valuation.current_price}
        healthScore={health!.score}
        healthRating={health!.rating}
        piotroski={health!.piotroski_score}
        riskLevel={riskQuery.data?.data?.risk_level ?? null}
      />

      <MarketOverview market={market} statement={statement} />

      <ValuationCards
        intrinsicValue={valuation.intrinsic_value}
        currentPrice={valuation.current_price}
        upside={valuation.upside}
        discountRate={valuation.discount_rate}
      />

      <FinancialHealth
        score={health!.score}
        rating={health!.rating}
        piotroski={health!.piotroski_score}
        altman={health!.altman_score}
        beneish={health!.beneish_score}
      />

      <RiskAnalysis
        beta={market.beta ?? null}
        risk={riskQuery.data?.data ?? null}
        isLoading={riskQuery.isPending}
        isError={riskQuery.isError}
        onRetry={() => riskQuery.refetch()}
      />

      <section id="insights" className="space-y-5 scroll-mt-32">
        <SectionHeading
          title="AI insights"
          description={`Ask about ${company.ticker} — the copilot uses the same filings, documents and statements as this analysis.`}
        />

        <div className="h-[32rem] xl:h-[38rem]">
          <AIChat ticker={ticker} />
        </div>
      </section>
    </div>
  );
}
