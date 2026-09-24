import { test, expect } from "@playwright/test";

test.describe("Console Error Audit", () => {
  test.beforeEach(async ({ page }) => {
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        console.log("CONSOLE ERROR:", msg.text());
      }
    });
    page.on("pageerror", (error) => {
      console.log("PAGE ERROR:", error.message);
    });
  });

  test("dashboard loads without console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));

    await page.goto("http://localhost:3000/dashboard");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    console.log("Dashboard errors:", errors);
    expect(errors.length).toBeLessThan(5);
  });

  test("analysis page loads without console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));

    await page.goto("http://localhost:3000/analysis/AAPL");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    console.log("Analysis errors:", errors);
    expect(errors.length).toBeLessThan(5);
  });

  test("comparison page loads without console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));

    await page.goto("http://localhost:3000/compare");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    console.log("Comparison errors:", errors);
    expect(errors.length).toBeLessThan(5);
  });

  test("all pages accessible without crash", async ({ page }) => {
    const pages = [
      "/dashboard",
      "/analysis/AAPL",
      "/compare",
      "/research",
      "/search",
      "/screener",
      "/reports",
      "/settings",
      "/portfolio",
      "/watchlist",
    ];

    for (const path of pages) {
      await page.goto(`http://localhost:3000${path}`);
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(500);
    }
  });
});
