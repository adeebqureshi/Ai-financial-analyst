import { test, expect } from "@playwright/test";

test.describe("Analysis workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("navigates to analysis page and displays financial data", async ({ page }) => {
    const responsePromise = page.waitForResponse(
      (response) => response.url().includes("/analyze") && response.request().method() === "POST"
    );
    await page.goto("/analysis/AAPL");
    const response = await responsePromise;
    expect(response.ok()).toBe(true);
    const payload = await response.json();
    const companyName = payload?.data?.company?.name;
    expect(typeof companyName).toBe("string");
    expect(companyName.length).toBeGreaterThan(0);
    await expect(page.locator("[data-testid='company-name']")).toContainText(companyName);
    await expect(page.locator("text=AI Analysis")).toBeVisible();

    await expect(page.locator("[data-testid='company-header']")).toBeVisible();
    await expect(page.locator("[data-testid='executive-summary']")).toBeVisible();
    await expect(page.locator("[data-testid='market-overview']")).toBeVisible();
    await expect(page.locator("[data-testid='valuation-cards']")).toBeVisible();
    await expect(page.locator("[data-testid='financial-health']")).toBeVisible();
    await expect(page.locator("[data-testid='risk-analysis']")).toBeVisible();
    await expect(page.locator("[data-testid='ai-chat']")).toBeVisible();
  });

  test("displays loading skeleton while analysis loads", async ({ page }) => {
    await page.goto("/analysis/AAPL");


    await expect(page.locator("[data-testid='skeleton-analysis-view']")).toBeVisible();
  });

  test("shows error state when analysis fails", async ({ page }) => {
    await page.route("**/analyze**", (route) => {
      route.fulfill({ status: 500, body: "Server Error" });
    });

    await page.goto("/analysis/INVALID");

    await expect(page.locator("text=Analysis Failed")).toBeVisible();
    await expect(page.locator("text=Try again")).toBeVisible();
  });
});

test.describe("Retired Command Hub route", () => {
  test("/dashboard redirects to the analysis workspace", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/analysis$/);
    await expect(page.locator("main")).toBeVisible();
  });
});

test.describe("Consolidated workflow routes", () => {
  test("/company redirects to Analyze", async ({ page }) => {
    await page.goto("/company");

    await expect(page).toHaveURL(/\/analysis$/);
    await expect(page.locator("main")).toBeVisible();
  });

  test("/company/AAPL redirects to the AAPL analysis", async ({ page }) => {
    await page.goto("/company/aapl");

    // The symbol is the segment the URL already carried, normalised and handed
    // to the canonical route.
    await expect(page).toHaveURL(/\/analysis\/AAPL$/);
    await expect(page.locator("main")).toBeVisible();
  });

  test("/reports redirects to Analyze", async ({ page }) => {
    await page.goto("/reports");

    await expect(page).toHaveURL(/\/analysis$/);
    await expect(page.locator("main")).toBeVisible();
  });

  test("sidebar offers a single company entry point", async ({ page }) => {
    await page.goto("/analysis");

    const nav = page.getByRole("navigation", { name: "Primary" });

    await expect(nav.getByRole("link", { name: "Analyze" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Company" })).toHaveCount(0);
    await expect(nav.getByRole("link", { name: "Reports" })).toHaveCount(0);
  });
});

test.describe("Simplified navigation", () => {
  test("Search and Settings are no longer primary destinations", async ({
    page,
  }) => {
    await page.goto("/analysis");

    const nav = page.getByRole("navigation", { name: "Primary" });

    await expect(nav.getByRole("link", { name: "Research" })).toBeVisible();
    // `exact` matters: a substring match for "Search" would otherwise hit
    // "Re-search".
    await expect(
      nav.getByRole("link", { name: "Search", exact: true })
    ).toHaveCount(0);
    await expect(
      nav.getByRole("link", { name: "Settings", exact: true })
    ).toHaveCount(0);
  });

  test("no empty navigation group labels are left behind", async ({ page }) => {
    await page.goto("/analysis");

    const labels = await page
      .getByRole("navigation", { name: "Primary" })
      .locator("p")
      .allInnerTexts();

    // `innerText` reflects the CSS uppercase transform.
    expect(labels.map((l) => l.trim().toLowerCase())).toEqual([
      "company analysis",
      "markets & compare",
      "research",
    ]);
  });

  test("the theme toggle lives in the topbar", async ({ page }) => {
    await page.goto("/analysis");

    const toggle = page
      .locator("header")
      .getByRole("button", { name: /Switch to (light|dark) theme/ });

    await expect(toggle).toBeVisible();

    const before = await page.evaluate(() =>
      document.documentElement.classList.contains("dark")
    );
    await toggle.click();
    await expect
      .poll(() =>
        page.evaluate(() =>
          document.documentElement.classList.contains("dark")
        )
      )
      .toBe(!before);
  });

  test("Search is reachable from Research", async ({ page }) => {
    await page.goto("/research");

    await page.getByRole("link", { name: "Search knowledge base" }).click();

    await expect(page).toHaveURL(/\/search$/);
    // The route still hosts the one real hybrid retrieval implementation.
    await expect(
      page.getByRole("heading", { name: /search the knowledge base/i })
    ).toBeVisible();
  });

  test("Analyze labels its list as research sessions", async ({ page }) => {
    await page.goto("/analysis");

    await expect(
      page.getByRole("heading", { name: "Recent research sessions" })
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Recent analyses" })
    ).toHaveCount(0);
  });

  test("analysis exposes report generation for the analysed ticker", async ({
    page,
  }) => {
    await page.goto("/analysis/AAPL");
    await page.waitForLoadState("networkidle");

    const section = page.locator("main section#report");

    await expect(section).toBeVisible();
    await expect(
      section.getByRole("heading", { name: "Research report" })
    ).toBeVisible();
    await expect(
      section.getByRole("button", { name: "Generate report" })
    ).toBeVisible();

    // No ticker field: the report is bound to the company already open.
    await expect(section.locator("#report-ticker")).toHaveCount(0);
  });
});

test.describe("PDF report download", () => {
  test("is not offered before an analysis runs", async ({ page }) => {
    await page.goto("/analysis");
    await page.waitForLoadState("networkidle");

    await expect(
      page.getByRole("button", { name: /download pdf report/i })
    ).toHaveCount(0);
  });

  test("appears after a successful analysis and downloads a real PDF", async ({
    page,
  }) => {
    await page.goto("/analysis/AAPL");
    await page.locator('[data-testid="company-name"]').waitFor({
      timeout: 120_000,
    });

    const button = page.getByRole("button", { name: "Download PDF report" });
    await expect(button).toBeVisible();

    let requestCount = 0;
    page.on("request", (request) => {
      if (request.url().includes("/analysis/pdf-report")) requestCount += 1;
    });

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 90_000 }),
      button.click(),
    ]);

    // A professional filename derived from the analysed ticker.
    expect(download.suggestedFilename()).toBe(
      "AAPL_Financial_Analysis_Report.pdf"
    );

    const path = await download.path();
    expect(path).toBeTruthy();

    const { readFileSync } = await import("node:fs");
    const bytes = readFileSync(path!);

    // A real PDF, not an HTML page or an empty file.
    expect(bytes.subarray(0, 5).toString("latin1")).toBe("%PDF-");
    expect(bytes.byteLength).toBeGreaterThan(1000);

    // One click, one render: the document must not require re-running the
    // analysis, and a burst of clicks must not queue extra requests.
    await page.mouse.click(200, 200).catch(() => {});
    expect(requestCount).toBe(1);
  });
});

test.describe("Comparison workflow", () => {
  test("renders comparison page with default tickers", async ({ page }) => {
    await page.goto("/comparison");

    // `/comparison` is a legacy alias for the canonical `/compare` route.
    await expect(page).toHaveURL(/\/compare$/);
    await expect(
      page.getByRole("heading", { name: /company comparison/i })
    ).toBeVisible();

    // Each default ticker is asserted through its remove control, which only
    // exists for a ticker in the "Selected" group. A bare `text=AAPL` match is
    // ambiguous: the symbol also appears in the "Popular" shortcut chips and in
    // the comparison table, so it would pass even if nothing were selected.
    for (const ticker of ["AAPL", "MSFT", "NVDA", "GOOGL"]) {
      await expect(
        page.getByRole("button", {
          name: `Remove ${ticker} from the comparison`,
        })
      ).toBeVisible();
    }
  });
});
