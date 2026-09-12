import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { ApiError, api } from "@/services/api";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const API_URL = "http://127.0.0.1:8000";

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