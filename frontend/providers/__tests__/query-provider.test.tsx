import { describe, it, expect } from "vitest";
import { shouldRetry } from "@/providers/query-provider";
import { ApiError } from "@/services/api";

describe("QueryProvider retry policy (shouldRetry)", () => {
  it("returns false after 3 failures", () => {
    expect(shouldRetry(3, new Error("test"))).toBe(false);
    expect(shouldRetry(4, new Error("test"))).toBe(false);
    expect(shouldRetry(10, new Error("test"))).toBe(false);
  });

  it("returns true for retryable ApiError (server error)", () => {
    const error = new ApiError("Server Error", 500, "/test");
    expect(shouldRetry(0, error)).toBe(true);
    expect(shouldRetry(1, error)).toBe(true);
    expect(shouldRetry(2, error)).toBe(true);
  });

  it("returns false for non-retryable ApiError (auth error)", () => {
    const error401 = new ApiError("Unauthorized", 401, "/test");
    const error403 = new ApiError("Forbidden", 403, "/test");
    expect(shouldRetry(0, error401)).toBe(false);
    expect(shouldRetry(0, error403)).toBe(false);
    expect(shouldRetry(1, error401)).toBe(false);
    expect(shouldRetry(2, error403)).toBe(false);
  });

  it("returns false for non-retryable ApiError (client error)", () => {
    const error400 = new ApiError("Bad Request", 400, "/test");
    const error404 = new ApiError("Not Found", 404, "/test");
    expect(shouldRetry(0, error400)).toBe(false);
    expect(shouldRetry(0, error404)).toBe(false);
    expect(shouldRetry(1, error400)).toBe(false);
    expect(shouldRetry(2, error404)).toBe(false);
  });

  it("returns true for network errors (TypeError with fetch)", () => {
    const error = new TypeError("Failed to fetch");
    expect(shouldRetry(0, error)).toBe(true);
    expect(shouldRetry(1, error)).toBe(true);
    expect(shouldRetry(2, error)).toBe(true);
  });

  it("returns false for network errors after 3 attempts", () => {
    const error = new TypeError("Failed to fetch");
    expect(shouldRetry(3, error)).toBe(false);
  });

  it("returns false for unknown errors", () => {
    expect(shouldRetry(0, "string error")).toBe(false);
    expect(shouldRetry(0, null)).toBe(false);
    expect(shouldRetry(0, undefined)).toBe(false);
    expect(shouldRetry(0, {})).toBe(false);
  });

  it("returns false for generic Error instances", () => {
    const error = new Error("Generic error");
    expect(shouldRetry(0, error)).toBe(false);
  });
});