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
