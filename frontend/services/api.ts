import type {
  AgentToolExecution,
  AnalyzeData,
  ApiResponse,
  CompareData,
  DocumentCitation,
  DocumentData,
  DocumentListData,
  ReportData,
  RiskAssessmentData,
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
    public readonly originalError?: Error,
    /**
     * True when this request was aborted by the client-side timeout rather than
     * failing on the server. The two need different wording — reporting our own
     * timeout as a server outage sends users and support chasing the wrong
     * problem.
     */
    public readonly timedOut = false
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

const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;
const LONG_REQUEST_TIMEOUT_MS = 120_000;

function getTimeoutMs(timeoutMs?: number): number {
  return timeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS;
}

async function parseSuccess<T>(
  response: Response,
  endpoint: string
): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (error) {
    throw new ApiError(
      "The server returned an invalid response.",
      response.status,
      endpoint,
      error instanceof Error ? error : undefined
    );
  }
}

async function request<T>(
  endpoint: string,
  init?: RequestInit,
  timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS
): Promise<T> {
  const headers: Record<string, string> = {
    ...(init?.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    ...(init?.headers as Record<string, string> | undefined),
  };


  if (typeof window !== "undefined") {
    let token = window.localStorage.getItem("access_token");

    if (!token) {
      try {
        const authResponse = await fetch("/api/auth/token", {
          method: "POST",
          cache: "no-store",
        });

        if (authResponse.ok) {
          const authData = await authResponse.json();
          token = authData.access_token;

          if (token) {
            window.localStorage.setItem("access_token", token);
          }
        }
      } catch {


      }
    }

    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(),
    getTimeoutMs(timeoutMs)
  );

  let response: Response;

  try {
    response = await fetch(getAPI() + endpoint, {
      ...init,
      headers,
      signal: controller.signal,
    });
  } catch (error) {
    const isAbort =
      error instanceof DOMException
        ? error.name === "AbortError"
        : error instanceof Error && error.name === "AbortError";

    if (isAbort) {
      throw new ApiError(
        "The request timed out. Please try again.",
        504,
        endpoint,
        error instanceof Error ? error : undefined,
        true
      );
    }

    throw new ApiError(
      "Unable to reach the server. Check your connection and try again.",
      0,
      endpoint,
      error instanceof Error ? error : undefined
    );
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    const text = await response.text();

    let message = `Request failed with status ${response.status}`;

    try {
      const parsed = JSON.parse(text);

      message =
        parsed?.message ??
        parsed?.detail ??
        (Array.isArray(parsed?.errors) && parsed.errors[0]?.message) ??
        message;
    } catch {
      if (text) {
        message = text;
      }
    }



    if (response.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem("access_token");
    }

    throw new ApiError(message, response.status, endpoint);
  }

  return parseSuccess<T>(response, endpoint);
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

export interface ChatSessionSummary {
  session_id: string;
  title: string | null;
  updated_at: string | null;
}

export interface ChatSessionListData {
  sessions: ChatSessionSummary[];
  total: number;
}

export interface ChatMessageData {
  role: "user" | "assistant";
  content: string;
  created_at?: string | null;
}

export interface ChatSessionMessagesData {
  session_id: string;
  messages: ChatMessageData[];
  total: number;
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

      if (delta) {
        handlers.onDelta?.(delta);
      }

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


async function requestChatStream(
  body: unknown,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const streamHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("access_token");

    if (token) {
      streamHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(getAPI() + "/chat/stream", {
    method: "POST",
    headers: streamHeaders,
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
      if (text) {
        message = text;
      }
    }

    handlers.onError?.(message);
    return;
  }

  if (!response.body) {
    handlers.onError?.(
      "Streaming is not supported by this browser."
    );
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

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
    // Report generation gathers market data, runs the valuation model and then
    // writes an LLM narrative. Measured end-to-end this takes ~60s, which is far
    // past the 30s default: the request was aborted before the backend replied
    // and the UI reported a generic "Server Error" for a call that actually
    // succeeded. Same long timeout the document upload already uses.
    return request(
      "/report",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
      LONG_REQUEST_TIMEOUT_MS
    );
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

  chatStream(
    body: unknown,
    handlers: ChatStreamHandlers,
    signal?: AbortSignal
  ): Promise<void> {
    return requestChatStream(body, handlers, signal);
  },

  listChatSessions(): Promise<ApiResponse<ChatSessionListData>> {
    return request("/chat/sessions");
  },

  listChatSessionMessages(
    sessionId: string
  ): Promise<ApiResponse<ChatSessionMessagesData>> {
    return request(
      `/chat/sessions/${encodeURIComponent(sessionId)}/messages`
    );
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

  uploadDocument(
    file: File
  ): Promise<ApiResponse<DocumentData>> {
    const form = new FormData();
    form.append("file", file);

    return request<ApiResponse<DocumentData>>(
      "/documents/upload",
      { method: "POST", body: form },
      LONG_REQUEST_TIMEOUT_MS
    );
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
