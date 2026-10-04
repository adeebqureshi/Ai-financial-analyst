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

  test("analysis page report generation flow", async ({ page }) => {
    await page.goto("http://localhost:3000/analysis/AAPL");
    await page.waitForLoadState("networkidle");

    // Report generation now lives inside the analysis workspace, bound to the
    // ticker already being analysed.
    const section = page.locator("main section#report");
    await expect(section).toBeVisible();
    await expect(
      section.getByRole("heading", { name: "Research report" })
    ).toBeVisible();

    await section.getByRole("button", { name: "Generate report" }).click();

    // Generation takes ~60s server-side, so assert the in-flight state rather
    // than waiting for the finished report.
    await expect(section.getByText(/Researching AAPL/)).toBeVisible();
  });

});
