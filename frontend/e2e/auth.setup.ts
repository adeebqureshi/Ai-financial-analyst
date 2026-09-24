import { request, type FullConfig } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

/** Create an isolated E2E identity through the real auth API. */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const apiBase = process.env.API_URL ?? "http://127.0.0.1:8000";
  const email = `playwright-${Date.now()}-${Math.random().toString(36).slice(2)}@e2e.invalid`;
  const password = process.env.E2E_PASSWORD ?? `E2e-${crypto.randomUUID()}-Aa1!`;
  const api = await request.newContext({ baseURL: apiBase, extraHTTPHeaders: { Accept: "application/json" } });
  try {
    console.log(`E2E auth setup: registering isolated user via ${apiBase}`);
    const registration = await api.post("/auth/register", { data: { email, password }, timeout: 15000 });
    if (!registration.ok()) throw new Error(`E2E registration failed (${registration.status()}): ${await registration.text()}`);
    const login = await api.post("/auth/token", { form: { username: email, password }, timeout: 15000 });
    if (!login.ok()) throw new Error(`E2E login failed (${login.status()}): ${await login.text()}`);
    const token = (await login.json()).access_token as string;
    if (!token) throw new Error("E2E login returned no access token");
    const statePath = path.resolve(__dirname, ".auth", "user.json");
    console.log(`E2E auth setup: writing state to ${statePath}`);
    await mkdir(path.dirname(statePath), { recursive: true });
    await writeFile(statePath, JSON.stringify({
      cookies: [],
      origins: [{ origin: "http://localhost:3000", localStorage: [{ name: "access_token", value: token }] }],
    }));
  } finally {
    await api.dispose();
  }
}
