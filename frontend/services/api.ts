import type {
  AnalyzeData,
  ApiResponse,
  ChatData,
  CompareData,
  CompanyData,
  DocumentData,
  DocumentListData,
  FinancialRatiosData,
  ReportData,
  RiskAssessmentData,
  ScreenData,
  SearchResultData,
} from "@/types/analysis";

const API =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

async function request<T>(
  endpoint: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(API + endpoint, {
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();

    let message = `Request failed with status ${response.status}`;

    try {
      const parsed = JSON.parse(text);
      message =
        parsed?.message ??
        parsed?.detail ??
        message;
    } catch {
      if (text) message = text;
    }

    console.error("Status:", response.status);
    console.error("Response:", text);

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health(): Promise<ApiResponse<unknown>> {
    return request("/health");
  },

  version(): Promise<ApiResponse<unknown>> {
    return request("/version");
  },

  company(
    ticker: string
  ): Promise<ApiResponse<CompanyData>> {
    return request(`/company/${ticker}`);
  },

  analyze(
    ticker: string
  ): Promise<ApiResponse<AnalyzeData>> {
    return request("/analyze", {
      method: "POST",
      body: JSON.stringify({
        ticker,
      }),
    });
  },

  valuation(
    body: unknown
  ): Promise<ApiResponse<unknown>> {
    return request("/valuation", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  intrinsicValue(
    body: unknown
  ): Promise<ApiResponse<unknown>> {
    return request("/intrinsic-value", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  financialRatios(
    body: unknown
  ): Promise<ApiResponse<FinancialRatiosData>> {
    return request("/financial-ratios", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  riskAnalysis(
    body: unknown
  ): Promise<ApiResponse<RiskAssessmentData>> {
    return request("/risk-analysis", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  report(
    body: unknown
  ): Promise<ApiResponse<ReportData>> {
    return request("/report", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  compare(
    tickers: string[]
  ): Promise<ApiResponse<CompareData>> {
    return request("/compare", {
      method: "POST",
      body: JSON.stringify({
        tickers,
      }),
    });
  },

  chat(
    body: unknown
  ): Promise<ApiResponse<ChatData>> {
    return request("/chat", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  search(
    query: string
  ): Promise<ApiResponse<SearchResultData>> {
    return request("/search", {
      method: "POST",
      body: JSON.stringify({
        query,
      }),
    });
  },

  screen(
    body: unknown
  ): Promise<ApiResponse<ScreenData>> {
    return request("/screen", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  uploadDocument(
    file: File
  ): Promise<ApiResponse<DocumentData>> {
    const form = new FormData();

    form.append("file", file);

    return fetch(API + "/documents/upload", {
      method: "POST",
      body: form,
    }).then(async (response) => {
      if (!response.ok) {
        const parsed = await response.json().catch(() => null);
        const message =
          parsed?.message ??
          parsed?.detail ??
          `Upload failed with status ${response.status}`;
        throw new Error(message);
      }

      return response.json() as Promise<
        ApiResponse<DocumentData>
      >;
    });
  },

  listDocuments(): Promise<
    ApiResponse<DocumentListData>
  > {
    return request("/documents");
  },

  deleteDocument(
    documentId: string
  ): Promise<ApiResponse<{ document_id: string }>> {
    return request(`/documents/${documentId}`, {
      method: "DELETE",
    });
  },
};
