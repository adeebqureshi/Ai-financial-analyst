import { test, expect } from "@playwright/test";

test.describe("Interactive Features Audit", () => {
  test("dashboard AI search form works", async ({ page }) => {
    await page.goto("http://localhost:3000/dashboard");
    await page.waitForLoadState("networkidle");
    const input = page.locator("input[placeholder*='Enter ticker']");
    await expect(input).toBeVisible();
    await input.fill("TSLA");
    await input.press("Enter");
    await page.waitForTimeout(2000);
  });

  test("analysis page ticker input validation", async ({ page }) => {
    await page.goto("http://localhost:3000/analysis");
    await page.waitForLoadState("networkidle");
    const input = page.locator("input[placeholder*='Enter ticker']");
    await expect(input).toBeVisible();
    await input.fill("123");
    const button = page.locator("button:has-text('Analyze')");
    await expect(button).toBeDisabled();
    await input.fill("");
    await input.fill("MSFT");
    await expect(button).toBeEnabled();
    await button.click();
    await page.waitForURL("**/analysis/MSFT**");
  });

  test("comparison add tickers", async ({ page }) => {
    await page.goto("http://localhost:3000/compare");
    await page.waitForLoadState("networkidle");
    const input = page.locator("input[placeholder='TSLA']");
    await expect(input).toBeVisible();
    await input.fill("AMD");
    await page.click("button:has-text('Add')");
    await page.waitForTimeout(500);
    await expect(page.locator("text=AMD")).toBeVisible();
  });

  test("reports page generate flow", async ({ page }) => {
    await page.goto("http://localhost:3000/reports");
    await page.waitForLoadState("networkidle");
    const input = page.locator("#report-ticker");
    await expect(input).toBeVisible();
    await input.fill("AAPL");
    await page.click("button:has-text('Generate report')");
    await page.waitForTimeout(3000);
  });

  test("screener form validation", async ({ page }) => {
    await page.goto("http://localhost:3000/screener");
    await page.waitForLoadState("networkidle");
    const tickerInput = page.locator("#criteria-ticker");
    await expect(tickerInput).toBeVisible();
    await tickerInput.fill("INVALID");
    const submitButton = page.locator("button[type='submit']");
    await expect(submitButton).toBeDisabled();
  });
});
