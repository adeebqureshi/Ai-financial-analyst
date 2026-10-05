import { test, expect, type Page, type APIRequestContext, type APIResponse } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

/**
 * Deleting a research session, against real persisted storage.
 *
 * Sessions are created through the live `POST /chat` endpoint with the e2e
 * user's own bearer token, so rows carry a real `owner_id` and ownership
 * scoping is exercised for real. Nothing is stubbed except the deliberate
 * failure-injection case.
 *
 * The persistence assertion deliberately re-reads the list from the server after
 * a full page reload — a row that merely vanished from React state would not
 * survive that.
 *
 * Note on volume: `POST /chat` and `DELETE /chat/sessions/{id}` share the same
 * `rate_limit_chat` budget (20/min by default), so this file seeds a small pool
 * of sessions once and shares it across tests instead of creating one per test,
 * and every mutating helper retries on 429 honouring `Retry-After`.
 */

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";
const AUTH_STATE = path.resolve(__dirname, ".auth", "user.json");

/** Bearer token seeded by `e2e/auth.setup.ts` into localStorage. */
function e2eToken(): string {
  const state = JSON.parse(readFileSync(AUTH_STATE, "utf8")) as {
    origins: { localStorage: { name: string; value: string }[] }[];
  };

  const entry = state.origins[0].localStorage.find((e) => e.name === "access_token");
  if (!entry) throw new Error("e2e storage state has no access_token");

  return entry.value;
}

/**
 * Run a mutating API call, waiting out a 429 rather than failing the test.
 *
 * `POST /chat` and `DELETE /chat/sessions/{id}` draw on one per-minute budget,
 * so a handful of quick tests can legitimately trip it.
 */
async function withRateLimitRetry(
  send: () => Promise<APIResponse>,
  what: string
): Promise<APIResponse> {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    let response: APIResponse;

    try {
      response = await send();
    } catch (error) {
      // A hung upstream (the LLM behind POST /chat) is transient, so retry it.
      console.log(`${what}: ${(error as Error).message.split("\n")[0]}`);
      await new Promise((resolve) => setTimeout(resolve, 5000));
      continue;
    }

    // Only a 429 is worth waiting out; any other status is the caller's business.
    if (response.status() !== 429) return response;

    const retryAfter = Number(response.headers()["retry-after"] ?? "5");
    const waitMs = Math.min(Math.max(retryAfter, 1), 20) * 1000;
    console.log(`${what}: rate limited, waiting ${waitMs / 1000}s`);
    await new Promise((resolve) => setTimeout(resolve, waitMs));
  }

  throw new Error(`${what}: gave up after 10 attempts`);
}

let runId = "";

/** Session ids this run created, so they can be cleaned up afterwards. */
const created = new Set<string>();

async function createSession(request: APIRequestContext, token: string, sessionId: string, question: string) {
  const response = await withRateLimitRetry(
    () =>
      request.post(`${API_URL}/chat`, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        data: { message: question, session_id: sessionId },
        timeout: 120_000,
      }),
    `create ${sessionId}`
  );

  expect(response.status(), `creating ${sessionId}`).toBe(200);
  created.add(sessionId);
}

async function destroySession(request: APIRequestContext, token: string, sessionId: string) {
  await withRateLimitRetry(
    () =>
      request.delete(`${API_URL}/chat/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    `delete ${sessionId}`
  );
  created.delete(sessionId);
}

/** The session list only, scoped by its section heading. */
function sessionList(page: Page) {
  return page.locator('section[aria-labelledby="recent-sessions-heading"]').getByRole("list");
}

/**
 * The delete-failure alert.
 *
 * Scoped to the session section because the persistent connection-status badge
 * also exposes `role="alert"`.
 */
function deleteAlert(page: Page) {
  return page.locator(
    'section[aria-labelledby="recent-sessions-heading"] [role="alert"]'
  );
}

/** Text of the visible session rows. */
async function visibleTitles(page: Page): Promise<string> {
  const list = sessionList(page);
  if ((await list.count()) === 0) return "";

  return list.innerText();
}

test.beforeEach(() => {
  runId = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
});

test.afterEach(async ({ request }) => {
  const token = e2eToken();

  for (const id of [...created]) {
    await destroySession(request, token, id);
  }
});

test.describe("Delete a research session", () => {
  test("cancels, deletes, and stays deleted after a reload", async ({ page, request }) => {
    test.setTimeout(240_000);

    const token = e2eToken();

    const targetId = `e2e-del-${runId}-target`;
    const otherId = `e2e-del-${runId}-other`;
    const targetQuestion = `Is NVDA overvalued ${runId}`;

    await createSession(request, token, targetId, targetQuestion);
    await createSession(request, token, otherId, `Compare AAPL and MSFT ${runId}`);

    await page.goto("/analysis");
    await expect(page.getByRole("heading", { name: "Recent research sessions" })).toBeVisible();

    // The real question is used as the title, not a generic placeholder.
    const rowLink = page.getByRole("link", { name: new RegExp(targetQuestion) });
    await expect(rowLink).toBeVisible({ timeout: 30_000 });

    // --- a delete control exists on the row
    const actions = page.getByRole("button", { name: `Actions for ${targetQuestion}` });
    await expect(actions).toBeVisible();

    // --- open the menu: Open + Delete
    await actions.click();
    const menu = page.getByRole("menu");
    await expect(menu.getByRole("menuitem", { name: /Open session/ })).toBeVisible();
    await menu.getByRole("menuitem", { name: /Delete/ }).click();

    // --- Cancel must not delete
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText("Delete research session?");
    await dialog.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toBeHidden();

    expect(await visibleTitles(page), "cancel must keep the session").toContain(
      targetQuestion
    );

    // --- Confirm deletes
    await actions.click();
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();

    await expect(dialog).toBeHidden({ timeout: 30_000 });
    await expect(rowLink, "deleted row must disappear").toHaveCount(0);

    // The sibling session survives.
    const afterDelete = await visibleTitles(page);
    expect(afterDelete).toContain("Compare AAPL and MSFT");
    expect(afterDelete).not.toContain(targetQuestion);

    // --- PERSISTENCE: full reload, then read from the server again.
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Recent research sessions" })
    ).toBeVisible({ timeout: 30_000 });

    await expect
      .poll(async () => visibleTitles(page), { timeout: 30_000 })
      .not.toContain(targetQuestion);

    // And it is gone from the API, not just the DOM.
    const listed = await request.get(`${API_URL}/chat/sessions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const ids = (await listed.json()).data.sessions.map(
      (s: { session_id: string }) => s.session_id
    );
    expect(ids, "deleted session must not return from the API").not.toContain(targetId);
    expect(ids).toContain(otherId);
  });

  test("reports a not-found failure and keeps the row", async ({ page, request }) => {
    test.setTimeout(180_000);

    const token = e2eToken();
    const id = `e2e-del-${runId}-gone`;
    const question = `Second question ${runId}`;

    await createSession(request, token, id, question);

    // Remove it server-side behind the UI's back.
    await destroySession(request, token, id);

    // The page then loads a list that no longer contains it.
    await page.goto("/analysis");
    await expect(page.getByRole("heading", { name: "Recent research sessions" })).toBeVisible();

    // Recreate it so there is a row on screen, then delete it again.
    await createSession(request, token, id, question);
    await page.reload();
    const row = page.getByRole("link", { name: new RegExp(question) });
    await expect(row).toBeVisible({ timeout: 30_000 });

    // Delete it behind the UI's back again, without a refetch.
    await request.delete(`${API_URL}/chat/sessions/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    await page.getByRole("button", { name: `Actions for ${question}` }).click();
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();

    // A 404 must be reported as a failure, not treated as success, and no
    // server wording may surface.
    const alert = deleteAlert(page);
    await expect(alert).toContainText("Couldn't delete this research session");
    await expect(alert).not.toContainText(/Session not found/i);
  });

  test("keeps the session and reports the failure when the server errors", async ({
    page,
    request,
  }) => {
    test.setTimeout(180_000);

    const token = e2eToken();
    const question = `Error path question ${runId}`;
    const id = `e2e-del-${runId}-error`;

    await createSession(request, token, id, question);

    await page.goto("/analysis");
    await expect(page.getByRole("link", { name: new RegExp(question) })).toBeVisible();

    // Fail only the DELETE, leaving the list read intact.
    await page.route(
      (url) => url.pathname.includes("/chat/sessions/") && url.pathname.split("/").length > 0,
      async (route) => {
        if (route.request().method() !== "DELETE") return route.fallback();

        return route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "internal traceback: boom" }),
        });
      }
    );

    await page.getByRole("button", { name: `Actions for ${question}` }).click();
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();

    const alert = deleteAlert(page);
    await expect(alert).toContainText(
      "Couldn't delete this research session. Please try again."
    );

    // The row is still there, and no server detail leaked.
    await expect(page.getByRole("link", { name: new RegExp(question) })).toBeVisible();
    await expect(alert).not.toContainText(/traceback|boom/i);
  });

  test("shows the empty state once the last session is deleted", async ({ page, request }) => {
    test.setTimeout(180_000);

    const token = e2eToken();
    const id = `e2e-del-${runId}-only`;
    const question = `Only question ${runId}`;

    await createSession(request, token, id, question);

    // Only the *list projection* is stubbed here, so the UI can be shown with a
    // library containing exactly one row.
    //
    // It must not be reached by emptying the real library: this project's dev
    // environment runs with AUTH_ENABLED=false, where every request resolves to
    // the anonymous owner and therefore shares one session namespace. Wiping
    // "my" sessions would delete every developer's history too. The DELETE
    // itself still goes to the real backend, and the real-store guarantees are
    // covered by the first test.
    let deleted = false;

    page.on("response", (response) => {
      if (response.request().method() === "DELETE" && response.status() === 204) {
        deleted = true;
      }
    });

    await page.route("**/chat/sessions", async (route) => {
      if (route.request().method() !== "GET") return route.fallback();

      const body = deleted
        ? { sessions: [], total: 0 }
        : {
            sessions: [
              {
                session_id: id,
                title: question,
                metadata: {},
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
            total: 1,
          };

      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          message: `${body.total} chat sessions`,
          data: body,
        }),
      });
    });

    await page.goto("/analysis");
    await expect(page.getByRole("link", { name: /Only question/ })).toBeVisible();

    await page.getByRole("button", { name: /Actions for Only question/ }).click();
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();

    await expect(page.getByRole("dialog")).toBeHidden();

    // The heading stays; the body becomes an honest empty state.
    await expect.poll(() => sessionList(page).count(), { timeout: 30_000 }).toBe(0);
    await expect(page.getByText(/No research sessions yet\./)).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Recent research sessions" })
    ).toBeVisible();

    // The row is gone for real, not just from the stubbed list.
    const gone = await withRateLimitRetry(
      () =>
        request.get(`${API_URL}/chat/sessions/${id}/messages`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      "verify messages gone"
    );
    expect(gone.status()).toBe(200);
    expect((await gone.json()).data.total).toBe(0);
  });

  test("is keyboard operable and leaves the row navigable", async ({ page, request }) => {
    test.setTimeout(180_000);

    const token = e2eToken();
    const question = `Keyboard question ${runId}`;
    const id = `e2e-del-${runId}-kbd`;

    await createSession(request, token, id, question);

    await page.goto("/analysis");
    const trigger = page.getByRole("button", { name: `Actions for ${question}` });
    await expect(trigger).toBeVisible();

    // Open with Enter, close with Escape — no deletion either way.
    await trigger.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("menu")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("menu")).toBeHidden();

    // Open the menu, choose Delete, then cancel with Escape.
    await trigger.focus();
    await page.keyboard.press("Enter");
    await page.getByRole("menu").getByRole("menuitem", { name: /Delete/ }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    // The safe action holds focus first.
    await expect(dialog.getByRole("button", { name: "Cancel" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();

    // Nothing was deleted, and the row is still a normal navigation link.
    const row = page.getByRole("link", { name: new RegExp(question) });
    await expect(row).toBeVisible();
    expect(await row.getAttribute("href")).toBe("/analysis");
  });

  test("stays usable and overflow-free across viewports", async ({ page, request }) => {
    test.setTimeout(180_000);

    const token = e2eToken();
    const question = `Responsive question ${runId}`;
    const id = `e2e-del-${runId}-responsive`;

    // One session covers every width; the test only cancels, so it is never
    // deleted and no extra chat budget is consumed.
    await createSession(request, token, id, question);

    for (const width of [390, 820, 1280, 1600]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/analysis");

      const trigger = page.getByRole("button", { name: `Actions for ${question}` });
      await expect(trigger, `visible at ${width}px`).toBeVisible();

      // No horizontal scrolling at any width.
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth
      );
      expect(overflow, `no horizontal overflow at ${width}px`).toBe(false);

      // The control is not overlapped or pushed off-screen.
      const box = await trigger.boundingBox();
      expect(box, `control has a box at ${width}px`).not.toBeNull();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1);

      await trigger.click();
      const menu = page.getByRole("menu");
      await expect(menu).toBeVisible();

      // The menu stays inside the viewport.
      const menuBox = await menu.boundingBox();
      expect(menuBox).not.toBeNull();
      expect(menuBox!.x).toBeGreaterThanOrEqual(0);
      expect(menuBox!.x + menuBox!.width).toBeLessThanOrEqual(width + 1);

      // And the confirmation dialog fits too.
      await menu.getByRole("menuitem", { name: /Delete/ }).click();
      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();

      const dialogBox = await dialog.boundingBox();
      expect(dialogBox).not.toBeNull();
      expect(dialogBox!.height, `dialog fits at ${width}px`).toBeLessThanOrEqual(900);
      expect(dialogBox!.x + dialogBox!.width).toBeLessThanOrEqual(width + 1);

      await dialog.getByRole("button", { name: "Cancel" }).click();
      await expect(dialog).toBeHidden();
    }
  });
});