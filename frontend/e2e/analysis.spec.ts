import { test, expect } from "@playwright/test";

test.describe("Analysis workflow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("navigates to analysis page and displays financial data", async ({ page }) => {
    await page.goto("/analysis/AAPL");

    await expect(page.locator("h1")).toContainText("Apple");
    await expect(page.locator("text=AI Analysis")).toBeVisible();

    await expect(page.locator("[data-testid='company-header']")).toBeVisible();
    await expect(page.locator("[data-testid='executive-summary']")).toBeVisible();
    await expect(page.locator("[data-testid='market-overview']")).toBeVisible();
    await expect(page.locator("[data-testid='valuation-cards']")).toBeVisible();
    await expect(page.locator("[data-testid='financial-health']")).toBeVisible();
    await expect(page.locator("[data-testid='risk-analysis']")).toBeVisible();
    await expect(page.locator("[data-testid='chart-tabs']")).toBeVisible();
    await expect(page.locator("[data-testid='ai-chat']")).toBeVisible();
  });

  test("displays loading skeleton while analysis loads", async ({ page }) => {
    await page.goto("/analysis/AAPL");

    await expect(page.locator(".animate-pulse")).toBeVisible();
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
  test("renders dashboard with metric cards", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.locator("text=Financial Workspace")).toBeVisible();
    await expect(page.locator("text=Your financial data workspace")).toBeVisible();
    await expect(page.locator("text=Portfolio Value")).toBeVisible();
    await expect(page.locator("text=Today's Gain")).toBeVisible();
    await expect(page.locator("text=Sharpe Ratio")).toBeVisible();
    await expect(page.locator("text=Cash Available")).toBeVisible();
  });

  test("displays AI search component", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.locator("text=Ask the AI Agent")).toBeVisible();
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