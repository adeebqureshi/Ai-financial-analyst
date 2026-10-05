import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";
const AUTH_STATE = path.resolve(__dirname, ".auth", "user.json");
const SHOTS = "probe-shots";

function token(): string {
  const s = JSON.parse(readFileSync(AUTH_STATE, "utf8")) as {
    origins: { localStorage: { name: string; value: string }[] }[];
  };
  return s.origins[0].localStorage.find((e) => e.name === "access_token")!.value;
}

test("manual verification: menu, dialog, delete, reload persistence", async ({
  page,
  request,
}) => {
  test.setTimeout(240_000);

  const tk = token();
  const stamp = Date.now();
  const a = `manual-${stamp}-alpha`;
  const b = `manual-${stamp}-beta`;
  const qA = `Summarize key risks for NVDA ${stamp}`;
  const qB = `Compare margins by segment ${stamp}`;

  for (const [id, q] of [
    [a, qA],
    [b, qB],
  ] as const) {
    const r = await request.post(`${API_URL}/chat`, {
      headers: { Authorization: `Bearer ${tk}`, "Content-Type": "application/json" },
      data: { message: q, session_id: id },
      timeout: 120_000,
    });
    console.log("seed", id, r.status());
  }

  try {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("http://localhost:3000/analysis");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2500);

    const rowA = page.getByRole("button", { name: `Actions for ${qA}` });
    await expect(rowA).toBeVisible();
    console.log("ROW TITLE:", qA);

    await page.screenshot({ path: `${SHOTS}/30-list.png` });

    // open menu
    await rowA.click();
    await expect(page.getByRole("menu")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/31-menu.png` });

    // dialog
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    console.log("DIALOG:", (await dialog.innerText()).replace(/\n/g, " | "));
    console.log("FOCUS ON OPEN:", await dialog.evaluate((d) => d.ownerDocument.activeElement?.textContent?.trim()));
    await page.screenshot({ path: `${SHOTS}/32-dialog.png` });

    // cancel
    await dialog.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByRole("button", { name: `Actions for ${qA}` })).toBeVisible();
    console.log("AFTER CANCEL, row still present: true");

    // delete for real
    await page.getByRole("button", { name: `Actions for ${qA}` }).click();
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(dialog).toBeHidden({ timeout: 30_000 });
    await expect(page.getByRole("button", { name: `Actions for ${qA}` })).toHaveCount(0);
    await expect(page.getByRole("button", { name: `Actions for ${qB}` })).toBeVisible();
    console.log("AFTER DELETE: target gone, sibling visible");
    await page.screenshot({ path: `${SHOTS}/33-after-delete.png` });

    // --- persistence across a real reload
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2500);
    const afterReload = await page.getByRole("button", { name: `Actions for ${qA}` }).count();
    console.log("AFTER RELOAD, deleted row count:", afterReload);
    expect(afterReload).toBe(0);
    await expect(page.getByRole("button", { name: `Actions for ${qB}` })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/34-after-reload.png` });

    // --- server + DB truth
    const listed = await request.get(`${API_URL}/chat/sessions`, {
      headers: { Authorization: `Bearer ${tk}` },
    });
    const ids = (await listed.json()).data.sessions.map(
      (s: { session_id: string }) => s.session_id
    );
    console.log("API still has deleted session:", ids.includes(a));
    console.log("API still has sibling session:", ids.includes(b));

    // messages of the deleted session are gone too
    const msgs = await request.get(`${API_URL}/chat/sessions/${a}/messages`, {
      headers: { Authorization: `Bearer ${tk}` },
    });
    console.log("deleted session message total:", (await msgs.json()).data.total);

    // --- documents must be untouched
    const docs = await request.get(`${API_URL}/documents`, {
      headers: { Authorization: `Bearer ${tk}` },
    });
    const docBody = (await docs.json()).data;
    console.log("documents still present:", docBody.total, docBody.documents.map((d: {filename: string}) => d.filename));

    // --- narrow viewport
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(800);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    console.log("390px horizontal overflow:", overflow);
    await page.getByRole("button", { name: `Actions for ${qB}` }).click();
    await page.screenshot({ path: `${SHOTS}/35-mobile-menu.png` });
    const menuBox = await page.getByRole("menu").boundingBox();
    console.log("menu box:", JSON.stringify(menuBox));
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    await page.screenshot({ path: `${SHOTS}/36-mobile-dialog.png` });
    const dBox = await page.getByRole("dialog").boundingBox();
    console.log("dialog box:", JSON.stringify(dBox), "viewport 390");
    await page.getByRole("dialog").getByRole("button", { name: "Cancel" }).click();
  } finally {
    for (const id of [a, b]) {
      await request
        .delete(`${API_URL}/chat/sessions/${id}`, { headers: { Authorization: `Bearer ${tk}` } })
        .catch(() => {});
    }
  }
});