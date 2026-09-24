import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { ApiError, api } from "@/services/api";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const API_URL = "/api/backend";

describe("services/api.ts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe("ApiError class", () => {
    it("creates an ApiError with correct properties", () => {
      const error = new ApiError("Test error", 404, "/test");
      expect(error.message).toBe("Test error");
      expect(error.status).toBe(404);
      expect(error.endpoint).toBe("/test");
      expect(error.name).toBe("ApiError");
    });

    it("isClientError returns true for 4xx status", () => {
      expect(new ApiError("Bad Request", 400, "/test").isClientError()).toBe(true);
      expect(new ApiError("Not Found", 404, "/test").isClientError()).toBe(true);
      expect(new ApiError("Unauthorized", 401, "/test").isClientError()).toBe(true);
      expect(new ApiError("Forbidden", 403, "/test").isClientError()).toBe(true);
    });

    it("isClientError returns false for non-4xx status", () => {
      expect(new ApiError("OK", 200, "/test").isClientError()).toBe(false);
      expect(new ApiError("Server Error", 500, "/test").isClientError()).toBe(false);
    });

    it("isServerError returns true for 5xx status", () => {
      expect(new ApiError("Server Error", 500, "/test").isServerError()).toBe(true);
      expect(new ApiError("Bad Gateway", 502, "/test").isServerError()).toBe(true);
      expect(new ApiError("Service Unavailable", 503, "/test").isServerError()).toBe(true);
    });

    it("isServerError returns false for non-5xx status", () => {
      expect(new ApiError("OK", 200, "/test").isServerError()).toBe(false);
      expect(new ApiError("Not Found", 404, "/test").isServerError()).toBe(false);
    });

    it("isAuthError returns true for 401 and 403", () => {
      expect(new ApiError("Unauthorized", 401, "/test").isAuthError()).toBe(true);
      expect(new ApiError("Forbidden", 403, "/test").isAuthError()).toBe(true);
    });

    it("isAuthError returns false for other statuses", () => {
      expect(new ApiError("Not Found", 404, "/test").isAuthError()).toBe(false);
      expect(new ApiError("Server Error", 500, "/test").isAuthError()).toBe(false);
      expect(new ApiError("OK", 200, "/test").isAuthError()).toBe(false);
    });

    it("isNotFound returns true for 404", () => {
      expect(new ApiError("Not Found", 404, "/test").isNotFound()).toBe(true);
    });

    it("isNotFound returns false for other statuses", () => {
      expect(new ApiError("Not Found", 400, "/test").isNotFound()).toBe(false);
      expect(new ApiError("Server Error", 500, "/test").isNotFound()).toBe(false);
    });

    it("isRetryable returns false for auth errors", () => {
      expect(new ApiError("Unauthorized", 401, "/test").isRetryable()).toBe(false);
      expect(new ApiError("Forbidden", 403, "/test").isRetryable()).toBe(false);
    });

    it("isRetryable returns false for client errors", () => {
      expect(new ApiError("Bad Request", 400, "/test").isRetryable()).toBe(false);
      expect(new ApiError("Not Found", 404, "/test").isRetryable()).toBe(false);
    });

    it("isRetryable returns true for server errors", () => {
      expect(new ApiError("Server Error", 500, "/test").isRetryable()).toBe(true);
      expect(new ApiError("Bad Gateway", 502, "/test").isRetryable()).toBe(true);
    });

    it("isRetryable returns true for network errors (no status)", () => {
      const error = new ApiError("Network error", 0, "/test");
      expect(error.isRetryable()).toBe(true);
    });
  });


  describe("runtime failure handling", () => {
    it("converts successful invalid JSON and an empty 204 to a safe retryable ApiError", async () => {
      for (const response of [
        { ok: true, status: 200, json: () => Promise.reject(new SyntaxError("Unexpected token <")) },
        { ok: true, status: 204, json: () => Promise.reject(new SyntaxError("Unexpected end of JSON input")) },
      ]) {
        mockFetch.mockResolvedValueOnce(response);
        const error: unknown = await api.health().catch((value) => value);
        expect(error).toBeInstanceOf(ApiError);
        if (!(error instanceof ApiError)) throw new Error("Expected ApiError");
        expect(error.message).toBe("The server returned an invalid response.");
        expect(error.isRetryable()).toBe(true);
      }
    });

    it("normalizes network failures and succeeds on a later explicit attempt", async () => {
      for (const original of [new TypeError("Failed to fetch"), new TypeError("connection reset")]) {
        mockFetch.mockRejectedValueOnce(original);
        const error: unknown = await api.health().catch((value) => value);
        expect(error).toBeInstanceOf(ApiError);
        if (!(error instanceof ApiError)) throw new Error("Expected ApiError");
        expect(error.message).toBe("Unable to reach the server. Check your connection and try again.");
        expect(error.isRetryable()).toBe(true);
        expect(error.originalError).toBe(original);
      }
      mockFetch.mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
      await expect(api.health()).resolves.toEqual({ ok: true });
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it("aborts a never-resolving request and permits a successful retry", async () => {
      vi.useFakeTimers();
      mockFetch.mockImplementationOnce((_url, init) => new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      }));
      const pending = api.health().catch((value) => value as ApiError);
      await vi.advanceTimersByTimeAsync(30_000);
      const error: unknown = await pending;
      expect(error).toBeInstanceOf(ApiError);
      if (!(error instanceof ApiError)) throw new Error("Expected ApiError");
      expect(error.status).toBe(504);
      expect(error.message).toBe("The request timed out. Please try again.");
      expect(error.isRetryable()).toBe(true);
      mockFetch.mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
      await expect(api.health()).resolves.toEqual({ ok: true });
      expect(mockFetch).toHaveBeenCalledTimes(2);
      vi.useRealTimers();
    });

    it("accepts a response completed before the timeout", async () => {
      vi.useFakeTimers();
      mockFetch.mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
      await expect(api.health()).resolves.toEqual({ ok: true });
      await vi.runAllTimersAsync();
      vi.useRealTimers();
    });

    it("parses a valid stale-token retry through the same success parser", async () => {
      window.localStorage.setItem("access_token", "stale");
      mockFetch
        .mockResolvedValueOnce({ ok: false, status: 401, text: () => Promise.resolve('{"message":"expired"}') })
        .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
      await expect(api.health()).resolves.toEqual({ ok: true });
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockFetch.mock.calls[1][1].headers.Authorization).toBeUndefined();
      window.localStorage.removeItem("access_token");
    });
  });

  describe("api object methods", () => {
    it("health calls correct endpoint", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.health();
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/health`, expect.any(Object));
    });

    it("version calls correct endpoint", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.version();
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/version`, expect.any(Object));
    });

    it("company calls correct endpoint with ticker", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.company("AAPL");
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/company/AAPL`, expect.any(Object));
    });

    it("analyze calls correct endpoint with POST and body", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.analyze("AAPL");
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/analyze`, expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ ticker: "AAPL" }),
      }));
    });

    it("compare calls correct endpoint with tickers array", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.compare(["AAPL", "MSFT"]);
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/compare`, expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ tickers: ["AAPL", "MSFT"] }),
      }));
    });

    it("search calls correct endpoint with query", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.search("apple");
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/search`, expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "apple" }),
      }));
    });

    it("uploadDocument uses FormData", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      const file = new File(["content"], "test.txt", { type: "text/plain" });
      await api.uploadDocument(file);

      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/documents/upload`, expect.objectContaining({
        method: "POST",
        body: expect.any(FormData),
      }));
    });

    it("listDocuments calls correct endpoint", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.listDocuments();
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/documents`, expect.any(Object));
    });

    it("deleteDocument calls correct endpoint with DELETE", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await api.deleteDocument("doc-123");
      expect(mockFetch).toHaveBeenCalledWith(`${API_URL}/documents/doc-123`, expect.objectContaining({
        method: "DELETE",
      }));
    });
  });
});