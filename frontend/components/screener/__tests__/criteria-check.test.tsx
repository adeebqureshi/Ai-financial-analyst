import { vi, describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { CriteriaCheck } from "@/components/screener/criteria-check";
import { api } from "@/services/api";

vi.mock("@/services/api", () => ({
  api: {
    analyze: vi.fn(),
    screen: vi.fn(),
  },
}));

type Wrapper = { children: ReactNode };
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return function QueryProvider({ children }: Wrapper) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
};

const statement = {
  revenue: 394328,
  operating_income: 114301,
  net_income: 96995,
  total_assets: 352583,
  total_liabilities: 279486,
  cash: 61640,
  debt: 106629,
  shares_outstanding: 15400,
  free_cash_flow: 108807,
};

const analyzeResponse = (beta: number | null, price: number | null) => ({
  success: true,
  message: "ok",
  data: {
    ticker: "AAPL",
    query: "AAPL",
    company: {
      ticker: "AAPL",
      name: "Apple Inc.",
      sector: "Technology",
      industry: null,
      market_cap: null,
      description: null,
    },
    market: {
      ticker: "AAPL",
      exchange: "NASDAQ",
      current_price: price,
      currency: "USD",
      market_cap: null,
      volume: null,
      beta,
      pe_ratio: null,
      eps: null,
      dividend_yield: null,
      week_52_high: null,
      week_52_low: null,
    },
    statement,
    valuation: {
      intrinsic_value: 200,
      upside: 33.3,
      recommendation: "BUY",
      current_price: price ?? 150,
      discount_rate: 10.5,
    },
    health: {
      score: 85,
      rating: "Strong",
      piotroski_score: 8,
      altman_score: 3.5,
      beneish_score: -2.1,
    },
    recommendation: "BUY",
  },
  errors: null,
  metadata: { timestamp: "", request_id: null, pagination: null },
});

const screenResponse = {
  success: true,
  message: "ok",
  data: {
    results: [
      {
        ticker: "AAPL",
        name: "Apple Inc.",
        piotroski_score: 8,
        altman_score: 3.5,
        beneish_score: -2.1,
        health_score: 85,
        health_rating: "Strong",
        intrinsic_value: 196.4,
        upside: 29.3,
        recommendation: "BUY",
      },
    ],
    total: 1,
  },
  errors: null,
  metadata: { timestamp: "", request_id: null, pagination: null },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.analyze).mockResolvedValue(analyzeResponse(1.24, 150));
  vi.mocked(api.screen).mockResolvedValue(screenResponse);
});

async function fetchAnalysis(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Ticker"), "AAPL");
  await user.click(screen.getByRole("button", { name: /fetch analysis/i }));
  await waitFor(() =>
    expect(screen.getByTestId("criteria-company-data")).toBeInTheDocument()
  );
}

// __TESTS__
