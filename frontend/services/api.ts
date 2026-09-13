import type {
  AgentToolExecution,
  AnalyzeData,
  ApiResponse,
  ChatData,
  CompareData,
  CompanyData,
  DocumentCitation,
  DocumentData,
  DocumentListData,
  FinancialRatiosData,
  ReportData,
  RiskAssessmentData,
  ScreenData,
  SearchResultData,
} from "@/types/analysis";

function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.API_URL ?? "http://127.0.0.1:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "/api/backend";
}

function getAPI(): string {
  return getApiBaseUrl();
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly endpoint: string,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = "ApiError";
  }

  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  isServerError(): boolean {
    return this.status >= 500;
  }

  isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isRetryable(): boolean {
    if (this.isAuthError()) return false;
    if (this.isClientError()) return false;
    return true;
  }
}

async function request<T>(
  endpoint: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(getAPI() + endpoint, {
    headers: {
      "Content-Type": "application/json",
    },
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

    throw new ApiError(message, response.status, endpoint);
  }

  return response.json() as Promise<T>;
}

export interface ChatStreamPlanData {
  tickers?: string[];
  intents?: string[];
  steps?: string[];
  tools_used?: AgentToolExecution[];
}

export interface ChatStreamDoneData {
  message: string;
  model: string | null;
  tickers?: string[];
  sources?: DocumentCitation[];
  steps?: string[];
  tools_used?: AgentToolExecution[];
}

export interface ChatStreamHandlers {
  onPlan?: (data: ChatStreamPlanData) => void;
  onDelta?: (delta: string) => void;
  onDone?: (data: ChatStreamDoneData) => void;
  onError?: (message: string) => void;
}

function handleStreamFrame(
  frame: string,
  handlers: ChatStreamHandlers
): void {
  let event = "message";
  let data = "";

  for (const line of frame.split("\n")) {
    if (line.startsWith("event: ")) {
      event = line.slice(7);
    } else if (line.startsWith("data: ")) {
      data += line.slice(6);
    }
  }

  if (!data) return;

  let payload: unknown;

  try {
    payload = JSON.parse(data);
  } catch {
    return;
  }

  switch (event) {
    case "plan":
      handlers.onPlan?.(payload as ChatStreamPlanData);
      break;
    case "token": {
      const delta = (payload as { delta?: string })?.delta ?? "";
      if (delta) handlers.onDelta?.(delta);
      break;
    }
    case "done":
      handlers.onDone?.(payload as ChatStreamDoneData);
      break;
    case "error": {
      const message =
        (payload as { message?: string })?.message ??
        "The chat stream failed unexpectedly.";
      handlers.onError?.(message);
      break;
    }
  }
}

/**
 * Consume the Server-Sent Events stream from ``POST /chat/stream``.
 *
 * Calls ``onDelta`` for every streamed token so the UI can render progressive
 * output, then ``onDone`` with the complete result.
 */
async function requestChatStream(
  body: unknown,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(getAPI() + "/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    const text = await response.text();

    let message = `Request failed with status ${response.status}`;

    try {
      const parsed = JSON.parse(text);
      message = parsed?.message ?? parsed?.detail ?? message;
    } catch {
      if (text) message = text;
    }

    handlers.onError?.(message);
    return;
  }

  if (!response.body) {
    handlers.onError?.("Streaming is not supported by this browser.");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");

    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      handleStreamFrame(frame, handlers);
      boundary = buffer.indexOf("\n\n");
    }
  }

  if (buffer.trim()) {
    handleStreamFrame(buffer, handlers);
  }
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

  chatStream(
    body: unknown,
    handlers: ChatStreamHandlers,
    signal?: AbortSignal
  ): Promise<void> {
    return requestChatStream(body, handlers, signal);
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

    return fetch(getAPI() + "/documents/upload", {
      method: "POST",
      body: form,
    }).then(async (response) => {
      if (!response.ok) {
        const parsed = await response.json().catch(() => null);
        const message =
          parsed?.message ??
          parsed?.detail ??
          `Upload failed with status ${response.status}`;
        throw new ApiError(message, response.status, "/documents/upload");
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
