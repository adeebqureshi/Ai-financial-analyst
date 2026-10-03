import { test, expect } from "@playwright/test";

test.describe("Interactive Features Audit", () => {
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

    // Located by accessible name: the placeholder text is illustrative
    // ("Enter ticker (e.g., AAPL, MSFT, NVDA)") and is not a stable hook.
    const input = page.getByLabel("Enter ticker");
    await expect(input).toBeVisible();

    await input.fill("AMD");
    await page.getByRole("button", { name: "Add company" }).click();

    // Assert AMD actually joined the selection rather than merely appearing
    // somewhere on the page.
    await expect(
      page.getByRole("button", { name: "Remove AMD from the comparison" })
    ).toBeVisible();
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

});
