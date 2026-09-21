import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
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

async function fetchAnalysis() {
  fireEvent.change(screen.getByLabelText(/Ticker/i), {
    target: { value: "AAPL" },
  });
  fireEvent.click(screen.getByRole("button", { name: /fetch analysis/i }));
  await waitFor(() =>
    expect(screen.getByTestId("criteria-company-data")).toBeInTheDocument()
  );
}

function fillAssumptions() {
  fireEvent.change(screen.getByLabelText(/FCF growth rate/i), {
    target: { value: "0.08" },
  });
  fireEvent.change(screen.getByLabelText(/Risk-free rate/i), {
    target: { value: "0.0425" },
  });
  fireEvent.change(screen.getByLabelText(/Expected market return/i), {
    target: { value: "0.10" },
  });
  fireEvent.change(screen.getByLabelText(/Effective tax rate/i), {
    target: { value: "0.21" },
  });
}

describe("CriteriaCheck", () => {
  it("fetches analysis and shows company data", async () => {
    render(<CriteriaCheck />, { wrapper: createWrapper() });
    await fetchAnalysis();
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
    expect(api.analyze).toHaveBeenCalledWith("AAPL");
  });

  it("blocks the check when assumptions are missing", async () => {
    render(<CriteriaCheck />, { wrapper: createWrapper() });
    await fetchAnalysis();
    fireEvent.click(
      screen.getByRole("button", { name: /run financial criteria check/i })
    );
    await waitFor(() =>
      expect(
        screen.getByText(/growth rate between 0 and 1/i)
      ).toBeInTheDocument()
    );
    expect(api.screen).not.toHaveBeenCalled();
  });

  it("runs the check and renders the backend result", async () => {
    render(<CriteriaCheck />, { wrapper: createWrapper() });
    await fetchAnalysis();
    fillAssumptions();
    fireEvent.click(
      screen.getByRole("button", { name: /run financial criteria check/i })
    );
    await waitFor(() =>
      expect(screen.getByTestId("criteria-result")).toBeInTheDocument()
    );
    expect(api.screen).toHaveBeenCalledOnce();
    expect(screen.getByText(/meets the criteria/i)).toBeInTheDocument();
  });
});
