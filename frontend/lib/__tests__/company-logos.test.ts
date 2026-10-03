import { describe, expect, it } from "vitest";

import {
  getCompanyLogoUrl,
  getCompanyMeta,
  getCompanyName,
  getMonogram,
  normalizeTicker,
} from "@/lib/company-logos";

describe("normalizeTicker", () => {
  it("uppercases and trims", () => {
    expect(normalizeTicker("  aapl ")).toBe("AAPL");
  });

  it("folds dot and dash separators to underscore", () => {
    // `/company/brk.b` reaches the UI as a route segment.
    expect(normalizeTicker("brk.b")).toBe("BRK_B");
    expect(normalizeTicker("BF-B")).toBe("BF_B");
  });

  it("returns empty string for missing input", () => {
    expect(normalizeTicker(null)).toBe("");
    expect(normalizeTicker(undefined)).toBe("");
    expect(normalizeTicker("")).toBe("");
  });
});

describe("getCompanyMeta", () => {
  it("resolves the reference tickers", () => {
    expect(getCompanyMeta("AAPL")?.domain).toBe("apple.com");
    expect(getCompanyMeta("msft")?.name).toBe("Microsoft");
    expect(getCompanyMeta("NVDA")?.name).toBe("NVIDIA");
  });

  it("shares one domain across share classes so the logo is reused", () => {
    expect(getCompanyMeta("GOOGL")?.domain).toBe(getCompanyMeta("GOOG")?.domain);
  });

  it("returns null for unknown and missing tickers", () => {
    expect(getCompanyMeta("ZZZZ")).toBeNull();
    expect(getCompanyMeta("")).toBeNull();
    expect(getCompanyMeta(null)).toBeNull();
  });
});

describe("getCompanyName", () => {
  it("prefers the backend name when supplied", () => {
    expect(getCompanyName("AAPL", "Apple Inc.")).toBe("Apple Inc.");
  });

  it("falls back to the registry name, then the ticker", () => {
    expect(getCompanyName("AAPL")).toBe("Apple");
    expect(getCompanyName("ZZZZ")).toBe("ZZZZ");
  });

  it("ignores a blank backend name rather than rendering nothing", () => {
    expect(getCompanyName("AAPL", "   ")).toBe("Apple");
  });
});

describe("getMonogram", () => {
  it("uses two characters so a single letter is not ambiguous", () => {
    expect(getMonogram("AAPL")).toBe("AA");
    expect(getMonogram("AMD")).toBe("AM");
  });

  it("handles true single-letter tickers", () => {
    expect(getMonogram("V")).toBe("V");
  });

  it("degrades to a question mark for empty input", () => {
    expect(getMonogram("")).toBe("?");
  });
});

describe("getCompanyLogoUrl", () => {
  it("builds a deterministic URL per domain", () => {
    const first = getCompanyLogoUrl("AAPL", 64);
    const second = getCompanyLogoUrl("AAPL", 64);

    expect(first).toBe(second);
    expect(first).toContain("apple.com");
  });

  it("reuses one URL for symbols sharing a domain", () => {
    expect(getCompanyLogoUrl("GOOGL", 64)).toBe(getCompanyLogoUrl("GOOG", 64));
  });

  it("never throws and returns null for unknown tickers", () => {
    expect(() => getCompanyLogoUrl("ZZZZ")).not.toThrow();
    expect(getCompanyLogoUrl("ZZZZ")).toBeNull();
  });

  it("returns null for missing input instead of a malformed URL", () => {
    expect(getCompanyLogoUrl(null)).toBeNull();
  });
});