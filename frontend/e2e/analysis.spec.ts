import { test, expect } from "@playwright/test";

test.describe("Analysis workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("navigates to analysis page and displays financial data", async ({ page }) => {
    await page.goto("/analysis/AAPL");

    // The company name is in the CompanyHeader with testid
    await expect(page.locator("[data-testid='company-name']")).toContainText("Apple");
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

    // Use the specific testid for the analysis skeleton
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

test.describe("Dashboard workflow", () => {
  test("renders dashboard without fabricated metrics", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.locator("text=Financial Workspace")).toBeVisible();
    await expect(page.locator("text=Your financial data workspace")).toBeVisible();
    await expect(page.locator("text=Watchlist")).toBeVisible();
    await expect(page.locator("text=Quick Actions")).toBeVisible();

    // De-fabrication guarantees: no portfolio/Sharpe/Fear & Greed placeholders
    await expect(page.locator("text=Portfolio Value")).toHaveCount(0);
    await expect(page.locator("text=Sharpe Ratio")).toHaveCount(0);
    await expect(page.locator("text=Cash Available")).toHaveCount(0);
    await expect(page.locator("text=Fear & Greed")).toHaveCount(0);
  });

  test("displays AI search component", async ({ page }) => {
    await page.goto("/dashboard");

    // AISearch component has this heading
    await expect(page.locator("text=Ask AI about any public company")).toBeVisible();
  });
});

test.describe("Comparison workflow", () => {
  test("renders comparison page with default tickers", async ({ page }) => {
    await page.goto("/comparison");

    await expect(page.locator("text=Company Comparison")).toBeVisible();
    await expect(page.locator("text=AAPL")).toBeVisible();
    await expect(page.locator("text=MSFT")).toBeVisible();
    await expect(page.locator("text=NVDA")).toBeVisible();
    await expect(page.locator("text=GOOGL")).toBeVisible();
  });
});