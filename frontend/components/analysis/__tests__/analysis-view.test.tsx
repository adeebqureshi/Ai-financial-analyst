import { vi, describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { AnalysisView } from "@/components/analysis/analysis-view";

vi.mock("@/hooks/use-analysis", () => ({
  useAnalysis: vi.fn(),
}));

vi.mock("@/components/analysis/company-header", () => ({
  CompanyHeader: function CompanyHeader({ company, recommendation, confidence }: { company: { name: string }; recommendation: string; confidence: number }) {
    return (
      <div data-testid="company-header">
        <h1>{company.name}</h1>
        <span>{recommendation}</span>
        <span>{confidence}%</span>
      </div>
    );
  },
}));

vi.mock("@/components/analysis/executive-summary", () => ({
  ExecutiveSummary: function ExecutiveSummary({ summary, upside, intrinsicValue, currentPrice }: { summary: string; upside: number; intrinsicValue: number; currentPrice: number }) {
    return (
      <div data-testid="executive-summary">
        <p>{summary}</p>
        <span>Upside: {upside}%</span>
        <span>Intrinsic: {intrinsicValue}</span>
        <span>Current: {currentPrice}</span>
      </div>
    );
  },
}));

vi.mock("@/components/analysis/market-overview", () => ({
  MarketOverview: function MarketOverview() {
    return <div data-testid="market-overview" />;
  },
}));

vi.mock("@/components/analysis/valuation-cards", () => ({
  ValuationCards: function ValuationCards() {
    return <div data-testid="valuation-cards" />;
  },
}));

vi.mock("@/components/analysis/financial-health", () => ({
  FinancialHealth: function FinancialHealth() {
    return <div data-testid="financial-health" />;
  },
}));

vi.mock("@/components/analysis/risk-analysis", () => ({
  RiskAnalysis: function RiskAnalysis() {
    return <div data-testid="risk-analysis" />;
  },
}));

vi.mock("@/components/charts", () => ({
  ChartTabs: function ChartTabs() {
    return <div data-testid="chart-tabs" />;
  },
}));

vi.mock("@/components/analysis/ai-chat", () => ({
  AIChat: function AIChat() {
    return <div data-testid="ai-chat" />;
  },
}));

import { useAnalysis } from "@/hooks/use-analysis";

type UseAnalysisReturn = ReturnType<typeof useAnalysis>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  function QueryProvider({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }

  return QueryProvider;
};

const mockAnalysisData = {
  data: {
    company: {
      name: "Apple Inc.",
      ticker: "AAPL",
      sector: "Technology",
      industry: "Consumer Electronics",
      description: "Apple designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories.",
    },
    recommendation: "BUY",
    valuation: {
      intrinsic_value: 200,
      current_price: 150,
      upside: 33.3,
      discount_rate: 10.5,
    },
    health: {
      score: 85,
      rating: "Strong",
      piotroski_score: 8,
      altman_score: 3.5,
      beneish_score: -2.1,
    },
    market: {
      beta: 1.2,
      market_cap: 3000000000000,
    },
    statement: {
      revenue: 383000000000,
      net_income: 97000000000,
      total_assets: 352000000000,
      total_liabilities: 290000000000,
      free_cash_flow: 110000000000,
    },
  },
};

describe("AnalysisView", () => {
  let wrapper: ReturnType<typeof createWrapper>;

  beforeEach(() => {
    vi.clearAllMocks();
    wrapper = createWrapper();
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: false, isError: false, data: mockAnalysisData, refetch: vi.fn() },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: true,
      error: null,
      data: mockAnalysisData,
    } as unknown as UseAnalysisReturn);
  });

  it("renders skeleton while loading", () => {
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: true, isError: false, data: undefined, refetch: vi.fn() },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: true,
      isError: false,
      isSuccess: false,
      error: null,
      data: undefined,
    } as unknown as UseAnalysisReturn);

    render(<AnalysisView ticker="AAPL" />, { wrapper });
    expect(screen.getByTestId("skeleton-analysis-view")).toBeInTheDocument();
  });

  it("renders ErrorDisplay when query fails", () => {
    const mockError = new Error("Failed to fetch analysis");
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: false, isError: true, data: undefined, refetch: vi.fn() },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: true,
      isSuccess: false,
      error: mockError,
      data: undefined,
    } as unknown as UseAnalysisReturn);

    render(<AnalysisView ticker="AAPL" />, { wrapper });

    expect(screen.getByText("Analysis Failed")).toBeInTheDocument();
    expect(screen.getByText(/unexpected error occurred/i)).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("renders ErrorDisplay when no data returned", () => {
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: false, isError: false, data: { data: null }, refetch: vi.fn() },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      isSuccess: true,
      error: null,
      data: { data: null },
    } as unknown as UseAnalysisReturn);

    render(<AnalysisView ticker="AAPL" />, { wrapper });

    expect(screen.getByText("Analysis Failed")).toBeInTheDocument();
    expect(screen.getByText("No analysis data was returned for this ticker.")).toBeInTheDocument();
  });

  it("renders complete analysis view on success", () => {
    render(<AnalysisView ticker="AAPL" />, { wrapper });

    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
    expect(screen.getByText("BUY")).toBeInTheDocument();
    expect(screen.getByTestId("executive-summary")).toBeInTheDocument();
    expect(screen.getByTestId("market-overview")).toBeInTheDocument();
    expect(screen.getByTestId("valuation-cards")).toBeInTheDocument();
    expect(screen.getByTestId("financial-health")).toBeInTheDocument();
    expect(screen.getByTestId("risk-analysis")).toBeInTheDocument();
    expect(screen.getByTestId("chart-tabs")).toBeInTheDocument();
    expect(screen.getByTestId("ai-chat")).toBeInTheDocument();
  });

  it("displays company info correctly", () => {
    render(<AnalysisView ticker="AAPL" />, { wrapper });

    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
    expect(screen.getByText("BUY")).toBeInTheDocument();
    expect(screen.getByTestId("company-header")).toBeInTheDocument();
  });

  it("shows retry button on error and calls refetch", () => {
    const mockRefetch = vi.fn();
    const mockError = new Error("Network error");
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: false, isError: true, data: undefined, refetch: mockRefetch },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: true,
      isSuccess: false,
      error: mockError,
      data: undefined,
    } as unknown as UseAnalysisReturn);

    render(<AnalysisView ticker="AAPL" />, { wrapper });

    const retryButton = screen.getByText("Try again");
    retryButton.click();
    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it("handles ApiError correctly in error state", () => {
    const apiError = new Error("Server Error");
    // @ts-expect-error - adding status property for test
    apiError.status = 500;
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: false, isError: true, data: undefined, refetch: vi.fn() },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: true,
      isSuccess: false,
      error: apiError,
      data: undefined,
    } as unknown as UseAnalysisReturn);

    render(<AnalysisView ticker="AAPL" />, { wrapper });

    expect(screen.getByText("Analysis Failed")).toBeInTheDocument();
    expect(screen.getByText("An unexpected error occurred.")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("does not show blank UI on failed API call", () => {
    const mockError = new Error("API unavailable");
    vi.mocked(useAnalysis).mockReturnValue({
      query: { isPending: false, isError: true, data: undefined, refetch: vi.fn() },
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: true,
      isSuccess: false,
      error: mockError,
      data: undefined,
    } as unknown as UseAnalysisReturn);

    render(<AnalysisView ticker="AAPL" />, { wrapper });

    const errorDisplay = screen.getByRole("alert");
    expect(errorDisplay).toBeInTheDocument();
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
});