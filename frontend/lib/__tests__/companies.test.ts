import { describe, expect, it } from "vitest";

import { resolveCompany, searchCompanies } from "@/lib/companies";

describe("resolveCompany", () => {
  it.each([
    ["AAPL", "AAPL"],
    ["aapl", "AAPL"],
    [" Apple ", "AAPL"],
    ["Apple", "AAPL"],
    ["apple", "AAPL"],
    ["Apple Inc.", "AAPL"],
    ["NVDA", "NVDA"],
    ["nvda", "NVDA"],
    ["NVIDIA", "NVDA"],
    ["nvidia", "NVDA"],
    ["NVIDIA Corporation", "NVDA"],
    ["MSFT", "MSFT"],
    ["microsoft", "MSFT"],
    ["Microsoft", "MSFT"],
    ["AMZN", "AMZN"],
    ["amazon", "AMZN"],
    ["TSLA", "TSLA"],
    ["tesla", "TSLA"],
    ["GOOGL", "GOOGL"],
    ["Google", "GOOGL"],
    ["CRM", "CRM"],
    ["Salesforce", "CRM"],
    ["SAP", "SAP"],
    ["SNY", "SNY"],
    ["Sanofi", "SNY"],
    ["SNDK", "SNDK"],
    ["SanDisk", "SNDK"],
  ])("resolves %s to %s", (input, ticker) => {
    expect(resolveCompany(input)?.ticker).toBe(ticker);
  });

  it("resolves Apple and AAPL to the identical canonical company", () => {
    expect(resolveCompany("Apple")).toEqual(resolveCompany("AAPL"));
    expect(resolveCompany("Apple")?.ticker).toBe("AAPL");
  });

  it("resolves NVIDIA and NVDA to the identical canonical company", () => {
    expect(resolveCompany("NVIDIA")).toEqual(resolveCompany("NVDA"));
    expect(resolveCompany("NVIDIA")?.ticker).toBe("NVDA");
  });

  it("returns null for unknown input instead of fabricating", () => {
    expect(resolveCompany("")).toBeNull();
    expect(resolveCompany("   ")).toBeNull();
    expect(resolveCompany("not a real company xyz")).toBeNull();
    expect(resolveCompany(null)).toBeNull();
  });
});

describe("searchCompanies", () => {
  it("matches a single letter and narrows on longer prefixes", () => {
    const one = searchCompanies("S", 50).map((c) => c.ticker);
    const two = searchCompanies("SA").map((c) => c.ticker);
    const three = searchCompanies("SAN").map((c) => c.ticker);
    expect(one).toContain("CRM");
    expect(one.length).toBeGreaterThanOrEqual(two.length);
    expect(two).toContain("CRM");
    expect(two).toContain("SAP");
    expect(three).toContain("SNDK");
    expect(three).toContain("SNY");
  });

  it("matches ticker prefix, name prefix and substring case-insensitively", () => {
    expect(searchCompanies("AAP")[0]?.ticker).toBe("AAPL");
    expect(searchCompanies("aapl")[0]?.ticker).toBe("AAPL");
    expect(searchCompanies("app")[0]?.ticker).toBe("AAPL");
    expect(searchCompanies("apple")[0]?.ticker).toBe("AAPL");
    expect(searchCompanies("nvi")[0]?.ticker).toBe("NVDA");
    expect(searchCompanies("tes")[0]?.ticker).toBe("TSLA");
    expect(searchCompanies("TSL")[0]?.ticker).toBe("TSLA");
  });

  it("returns an empty list for blank or unknown queries", () => {
    expect(searchCompanies("")).toEqual([]);
    expect(searchCompanies("   ")).toEqual([]);
    expect(searchCompanies("zzz-no-such-company")).toEqual([]);
  });
});
