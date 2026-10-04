import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { DownloadReportButton } from "@/components/analysis/download-report-button";
import { api } from "@/services/api";

import type { AnalysisPdfRequest } from "@/types/analysis";

const analysis: AnalysisPdfRequest = {
  ticker: "NVDA",
  company: {
    ticker: "NVDA",
    name: "NVIDIA Corporation",
    sector: "Technology",
    industry: "Semiconductors",
    market_cap: 4.29e12,
    description: "Designs GPUs.",
  },
  market: {
    ticker: "NVDA",
    exchange: "NASDAQ",
    current_price: 175.43,
    currency: "USD",
    market_cap: 4.29e12,
    volume: 51_234_000,
    beta: 2.11,
    pe_ratio: 45.6,
    eps: 3.85,
    dividend_yield: 0.0002,
    week_52_high: 180.42,
    week_52_low: 86.62,
  },
  statement: {
    revenue: 3.83e11,
    operating_income: 1.83e11,
    net_income: 9.7e10,
    total_assets: 3.52e11,
    total_liabilities: 2.9e11,
    cash: 7.27e10,
    debt: 8.46e9,
    shares_outstanding: 2.45e10,
    free_cash_flow: 1.1e11,
  },
  valuation: {
    intrinsic_value: 142.3,
    upside: -18.87,
    recommendation: "HOLD",
    current_price: 175.43,
    discount_rate: 0.105,
  },
  health: {
    score: 85,
    rating: "Strong",
    piotroski_score: 8,
    altman_score: 3.52,
    beneish_score: -1.86,
  },
  recommendation: "HOLD",
  risk: null,
};

function pdfBlob() {
  // A minimal but structurally real PDF header, enough for the guards.
  return new Blob([new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x37])], {
    type: "application/pdf",
  });
}

describe("DownloadReportButton", () => {
  let clickSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // The component drives a synthetic anchor click to trigger the download;
    // jsdom does not implement navigation, so it is captured here.
    clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
    // jsdom does not implement the object-URL APIs at all, so they are defined
    // rather than spied on.
    URL.createObjectURL = vi.fn(() => "blob:mock");
    URL.revokeObjectURL = vi.fn();
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends the completed analysis result and no ticker-only request", async () => {
    const spy = vi
      .spyOn(api, "analysisPdf")
      .mockResolvedValue({ blob: pdfBlob(), filename: "NVDA_Financial_Analysis_Report.pdf" });

    render(<DownloadReportButton analysis={analysis} />);
    fireEvent.click(
      screen.getByRole("button", { name: /download pdf report/i })
    );

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));

    // The whole result is posted, so the renderer never re-runs the analysis.
    expect(spy).toHaveBeenCalledWith(analysis);
    expect(clickSpy).toHaveBeenCalledTimes(1);
  });

  it("names the file from the server Content-Disposition", async () => {
    vi.spyOn(api, "analysisPdf").mockResolvedValue({
      blob: pdfBlob(),
      filename: "NVDA_Financial_Analysis_Report.pdf",
    });

    render(<DownloadReportButton analysis={analysis} />);
    fireEvent.click(
      screen.getByRole("button", { name: /download pdf report/i })
    );

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());

    const link = clickSpy.mock.instances[0] as HTMLAnchorElement;
    expect(link.download).toBe("NVDA_Financial_Analysis_Report.pdf");
  });

  it("falls back to a sanitised ticker filename", async () => {
    vi.spyOn(api, "analysisPdf").mockResolvedValue({ blob: pdfBlob(), filename: null });

    render(<DownloadReportButton analysis={analysis} />);
    fireEvent.click(
      screen.getByRole("button", { name: /download pdf report/i })
    );

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());

    const link = clickSpy.mock.instances[0] as HTMLAnchorElement;
    expect(link.download).toBe("NVDA_Financial_Analysis_Report.pdf");
  });

  it("blocks a second request while one is in flight", async () => {
    let release: (value: { blob: Blob; filename: string }) => void = () => {};
    const spy = vi
      .spyOn(api, "analysisPdf")
      .mockReturnValue(
        new Promise((resolve) => {
          release = resolve;
        })
      );

    render(<DownloadReportButton analysis={analysis} />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    await waitFor(() =>
      expect(button).toHaveAttribute("aria-busy", "true")
    );
    expect(button).toBeDisabled();

    // A second click while generating must not queue another render.
    fireEvent.click(button);
    expect(spy).toHaveBeenCalledTimes(1);

    release({ blob: pdfBlob(), filename: "NVDA_Financial_Analysis_Report.pdf" });

    await waitFor(() => expect(button).toBeEnabled());
  });

  it("shows a plain error and no stack trace when generation fails", async () => {
    vi.spyOn(api, "analysisPdf").mockRejectedValue(
      new Error("500 Internal Server Error at /analysis/pdf-report:\n  File \"x.py\", line 4")
    );

    render(<DownloadReportButton analysis={analysis} />);
    fireEvent.click(
      screen.getByRole("button", { name: /download pdf report/i })
    );

    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(
      "Unable to generate the report. Please try again."
    );
    expect(alert.textContent).not.toMatch(/File "x\.py"|Traceback/);
  });

  it("rejects a non-PDF body instead of saving an unopenable file", async () => {
    vi.spyOn(api, "analysisPdf").mockResolvedValue({
      blob: new Blob(["not a pdf"], { type: "text/html" }),
      filename: "NVDA_Financial_Analysis_Report.pdf",
    });

    render(<DownloadReportButton analysis={analysis} />);
    fireEvent.click(
      screen.getByRole("button", { name: /download pdf report/i })
    );

    await screen.findByRole("alert");
    expect(clickSpy).not.toHaveBeenCalled();
  });

  it("has an accessible name that does not rely on the icon alone", () => {
    render(<DownloadReportButton analysis={analysis} />);

    const button = screen.getByRole("button", {
      name: "Download PDF report",
    });

    expect(button).toBeInTheDocument();
  });
});