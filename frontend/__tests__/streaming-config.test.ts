import { afterEach, describe, expect, it, vi } from "vitest";

/**
 * Regression guard for the SSE streaming failure in the dev server.
 *
 * Next's compression middleware matches `text/*`, so it gzipped the
 * `text/event-stream` response produced by the `/api/backend` rewrite. gzip
 * buffers, which defeats Server-Sent Events: the dev server delivered the
 * whole AI research stream as a single ~31 KB chunk ~29 s after the request,
 * and on longer RAG answers the stalled connection was reset, which the
 * browser reported as `ERR_INCOMPLETE_CHUNKED_ENCODING` / "Generation failed".
 *
 * Compression must therefore be off in development (where on-the-fly
 * compilation makes the stall long enough to trip the failure) and unchanged
 * in production.
 */
async function loadConfig(nodeEnv: string) {
  vi.resetModules();
  vi.stubEnv("NODE_ENV", nodeEnv);
  try {
    const mod = await import("../next.config");
    return mod.default;
  } finally {
    vi.unstubAllEnvs();
  }
}

afterEach(() => {
  vi.resetModules();
  vi.unstubAllEnvs();
});

describe("next.config compression", () => {
  it("disables compression in development so SSE is not buffered", async () => {
    const config = await loadConfig("development");

    expect(config.compress).toBe(false);
  });

  it("keeps compression enabled in production (unchanged behaviour)", async () => {
    const config = await loadConfig("production");

    expect(config.compress).toBe(true);
  });

  it("still proxies /api/backend to the FastAPI backend", async () => {
    const config = await loadConfig("development");
    const rewrites = await config.rewrites?.();

    expect(rewrites).toEqual([
      {
        source: "/api/backend/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
    ]);
  });
});
