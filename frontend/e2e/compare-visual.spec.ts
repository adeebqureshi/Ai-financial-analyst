import { test, expect } from "@playwright/test";

const SIZES = [
  { name: "desktop-1440", width: 1440, height: 1100 },
  { name: "desktop-1280", width: 1280, height: 1000 },
  { name: "tablet-834", width: 834, height: 1100 },
  { name: "mobile-390", width: 390, height: 900 },
];

for (const size of SIZES) {
  test(`compare visual ${size.name}`, async ({ page }) => {
    await page.setViewportSize({ width: size.width, height: size.height });
    await page.goto("http://localhost:3000/compare");
    await page.waitForLoadState("networkidle");
    await page.waitForFunction(() => !document.querySelector('[aria-busy="true"]'), undefined, {
      timeout: 90000,
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `shots/compare-${size.name}.png`, fullPage: true });

    // no horizontal overflow
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
}

test("compare interactive states", async ({ page }) => {
  // This drives the real `/compare` pipeline: adding, removing and clearing
  // companies each re-fetch and re-derive valuation and health for every
  // symbol, so the whole flow takes ~35s against a live backend. The global
  // 60s budget expired part-way through and reported the failure against
  // whichever step happened to be running, so this test carries its own
  // realistic timeout. The assertions are unchanged.
  test.setTimeout(180_000);

  await page.setViewportSize({ width: 1440, height: 1100 });
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));

  await page.goto("http://localhost:3000/compare");
  await page.waitForLoadState("networkidle");
  await page.waitForFunction(() => !document.querySelector('[aria-busy="true"]'), undefined, {
    timeout: 90000,
  });
  await page.waitForTimeout(500);
  await page.screenshot({ path: "shots/compare-loaded.png", fullPage: true });

  const input = page.getByLabel("Search company or ticker", { exact: true });
  await input.fill("AMD");
  await page.click("button:has-text('Add company')");
  await page.waitForFunction(() => !document.querySelector('[aria-busy="true"]'), undefined, {
    timeout: 90000,
  });
  await page.screenshot({ path: "shots/compare-added.png", fullPage: true });

  await page.click("button[role='tab']:has-text('Valuation')");
  await page.waitForTimeout(400);
  await page.screenshot({ path: "shots/compare-tab-valuation.png", fullPage: true });

  await page.click("button[role='tab']:has-text('Financial health')");
  await page.waitForTimeout(400);
  await page.screenshot({ path: "shots/compare-tab-health.png", fullPage: true });

  await page.click("button[role='tab']:has-text('Key metrics')");
  await page.waitForTimeout(300);

  await page.click("button:has-text('TSLA')");
  await page.waitForTimeout(1500);

  await page.click("button[aria-label='Remove AMD from the comparison']");
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "shots/compare-removed.png", fullPage: true });

  await page.click("button:has-text('Clear all')");
  await page.waitForTimeout(600);
  await page.screenshot({ path: "shots/compare-cleared.png", fullPage: true });

  console.log("CONSOLE ERRORS:", errors);
  expect(errors.length).toBeLessThan(5);
});

test("all pages still render", async ({ page }) => {
  for (const path of [
    "/analysis",
    "/analysis/AAPL",
    "/compare",
    "/research",
    "/search",
  ]) {
    await page.goto(`http://localhost:3000${path}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main")).toBeVisible();
  }
});
