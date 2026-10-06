import { test, expect, type Page } from "@playwright/test";

/**
 * Layout regression: the AI Insights chat must never overlap the Research
 * report section below it, regardless of how long the conversation grows.
 *
 * The chat card lives in a fixed-height wrapper; long answers must scroll
 * INSIDE the conversation area, and `#report` must always start below the
 * card's bottom edge.
 */

const TICKER = "NVDA";

type Geometry = {
  overlap: boolean;
  chatBottom: number;
  chatHeight: number;
  reportTop: number;
  listScrollHeight: number;
  listClientHeight: number;
  composerVisible: boolean;
  pageScrollWidth: number;
  viewportWidth: number;
};

async function measure(page: Page): Promise<Geometry> {
  return page.evaluate(() => {
    const chat = document.querySelector<HTMLElement>("[data-testid='ai-chat']");
    const report = document.querySelector<HTMLElement>("#report");

    if (!chat || !report) {
      throw new Error("chat or report section missing from the DOM");
    }

    // The conversation scroll area: the ChatSurface child with overflow-y auto.
    const list = Array.from(chat.querySelectorAll("div")).find(
      (element) => getComputedStyle(element).overflowY === "auto"
    );

    const chatRect = chat.getBoundingClientRect();
    const reportRect = report.getBoundingClientRect();
    const horizontal =
      chatRect.right > reportRect.left && chatRect.left < reportRect.right;
    const composer = chat.querySelector("textarea");

    return {
      overlap: horizontal && chatRect.bottom > reportRect.top + 1,
      chatBottom: chatRect.bottom,
      chatHeight: chatRect.height,
      reportTop: reportRect.top,
      listScrollHeight: list?.scrollHeight ?? 0,
      listClientHeight: list?.clientHeight ?? 0,
      composerVisible: Boolean(
        composer && composer.getBoundingClientRect().height > 0
      ),
      pageScrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    };
  });
}

/**
 * Append a very tall fake answer (with a long URL-like token) to the
 * conversation list. React never clears foreign children it does not own, so
 * this simulates a multi-thousand-pixel streamed response deterministically.
 */
async function injectTallContent(page: Page): Promise<void> {
  await page.evaluate(() => {
    const chat = document.querySelector<HTMLElement>("[data-testid='ai-chat']");
    const list = Array.from(chat?.querySelectorAll("div") ?? []).find(
      (element) => getComputedStyle(element).overflowY === "auto"
    );

    if (!list) throw new Error("conversation scroll area not found");

    const probe = document.createElement("div");
    probe.setAttribute("data-testid", "layout-probe");
    probe.style.height = "4000px";
    probe.style.minWidth = "0";
    // Match a message row: never compressed by the flex column, so it must
    // overflow the conversation area and force internal scrolling.
    probe.style.flexShrink = "0";
    probe.textContent =
      "NVIDIA's DCF analysis estimates an intrinsic value. ".repeat(30) +
      "https://example.com/research/" +
      "a".repeat(300);

    list.appendChild(probe);
  });
}

async function loadAnalysis(page: Page): Promise<void> {
  const analyze = page.waitForResponse(
    (response) =>
      response.url().includes("/analyze") &&
      response.request().method() === "POST"
  );
  await page.goto(`/analysis/${TICKER}`);
  expect((await analyze).ok()).toBe(true);
  await expect(page.locator("[data-testid='ai-chat']")).toBeVisible();
  await expect(page.locator("#report")).toBeVisible();
  // Let the session-restore / analysis queries settle before measuring.
  await page.waitForTimeout(1500);
}

test.describe("AI Insights / Research report layout", () => {
  test("a very long AI response scrolls inside the chat and never overlaps the report", async ({
    page,
  }) => {
    await loadAnalysis(page);
    await injectTallContent(page);

    const geometry = await measure(page);

    expect(geometry.overlap).toBe(false);
    expect(geometry.reportTop).toBeGreaterThanOrEqual(geometry.chatBottom - 1);
    // The 4000px payload must scroll INSIDE the conversation, not escape it.
    expect(geometry.listScrollHeight).toBeGreaterThan(
      geometry.listClientHeight + 1000
    );
    // Header and composer stay reachable within the card.
    expect(geometry.composerVisible).toBe(true);
    // No horizontal page overflow from the long URL-like token.
    expect(geometry.pageScrollWidth).toBeLessThanOrEqual(
      geometry.viewportWidth + 1
    );
  });

  test("layout holds while an answer streams and after it completes", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    await loadAnalysis(page);

    const composer = page.getByRole("textbox", {
      name: "Message the AI financial analyst",
    });
    await composer.fill(
      "Give a detailed assessment of NVIDIA's valuation, financial health and the main risks, with specific numbers."
    );
    await composer.press("Enter");

    const stop = page.getByRole("button", { name: "Stop generating" });
    await expect(stop).toBeVisible({ timeout: 60_000 });

    // Mid-stream: content is growing token-by-token.
    const streaming = await measure(page);
    expect(streaming.overlap).toBe(false);
    expect(streaming.reportTop).toBeGreaterThanOrEqual(
      streaming.chatBottom - 1
    );

    await expect(stop).toBeHidden({ timeout: 120_000 });
    await page.waitForTimeout(500);

    const done = await measure(page);
    expect(done.overlap).toBe(false);
    expect(done.reportTop).toBeGreaterThanOrEqual(done.chatBottom - 1);

    // The free-tier model occasionally returns an empty turn; only demand
    // internal scrolling when we actually received a long answer. The
    // injected-content tests already cover the scrolling contract
    // deterministically.
    const contentLength = await page.evaluate(() => {
      const chat = document.querySelector("[data-testid='ai-chat']");
      const list = Array.from(chat?.querySelectorAll("div") ?? []).find(
        (element) => getComputedStyle(element).overflowY === "auto"
      );
      return list?.textContent?.length ?? 0;
    });

    if (contentLength > 1500) {
      expect(done.listScrollHeight).toBeGreaterThan(done.listClientHeight);
    }

    expect(done.composerVisible).toBe(true);
  });

  test("section tabs keep working with a long conversation loaded", async ({
    page,
  }) => {
    await loadAnalysis(page);
    await injectTallContent(page);

    const nav = page.getByRole("navigation", { name: "Analysis sections" });

    for (const label of [
      "Summary",
      "Market",
      "Valuation",
      "Health",
      "Risk",
      "AI Insights",
      "Report",
    ]) {
      await nav.getByRole("link", { name: label }).click();
      await page.waitForTimeout(150);
    }

    await expect(
      page
        .locator("#report")
        .getByRole("heading", { name: "Research report" })
    ).toBeVisible();

    const geometry = await measure(page);
    expect(geometry.overlap).toBe(false);
    expect(geometry.reportTop).toBeGreaterThanOrEqual(geometry.chatBottom - 1);
  });
});

test.describe("Responsive: AI Insights vs report", () => {
  test.describe("tablet", () => {
    test.use({ viewport: { width: 768, height: 1024 } });

    test("no overlap with a long response", async ({ page }) => {
      await loadAnalysis(page);
      await injectTallContent(page);

      const geometry = await measure(page);
      expect(geometry.overlap).toBe(false);
      expect(geometry.reportTop).toBeGreaterThanOrEqual(
        geometry.chatBottom - 1
      );
      expect(geometry.pageScrollWidth).toBeLessThanOrEqual(
        geometry.viewportWidth + 1
      );
    });
  });

  test.describe("mobile", () => {
    test.use({ viewport: { width: 375, height: 812 } });

    test("no overlap with a long response", async ({ page }) => {
      await loadAnalysis(page);
      await injectTallContent(page);

      const geometry = await measure(page);
      expect(geometry.overlap).toBe(false);
      expect(geometry.reportTop).toBeGreaterThanOrEqual(
        geometry.chatBottom - 1
      );
      expect(geometry.pageScrollWidth).toBeLessThanOrEqual(
        geometry.viewportWidth + 1
      );
    });
  });
});

