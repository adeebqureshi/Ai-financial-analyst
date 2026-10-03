import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // Next 16 applies a 30s timeout to rewritten requests
    // (`router-utils/proxy-request.js`, `proxyTimeout || 30000`). Requests to
    // the backend go through the `/api/backend/:path*` rewrite below, and two
    // real operations legitimately exceed 30s: `POST /report` (market data +
    // valuation + LLM narrative) measured 35–64s, and `POST /documents/upload`
    // parses and indexes a PDF. Both were cut off by the proxy at exactly 30.0s
    // and surfaced to the browser as a bare "Internal Server Error", which looks
    // like a backend fault and is not one.
    //
    // Raised to match `LONG_REQUEST_TIMEOUT_MS` in `services/api.ts` so the
    // client-side and proxy budgets agree and the client, not the proxy, is what
    // gives up first.
    proxyTimeout: 120_000,
  },

  // The floating dev-tools badge is pinned to the bottom-left of the viewport,
  // where it overlaps the sidebar's "Backend connected" status and — on narrow
  // screens — floats over the first feature card. It is a development-only
  // overlay, so it is positioned to the bottom-right where the app's own
  // copilot FAB sits, rather than removed (it is useful during development).
  devIndicators: {
    position: "bottom-right",
  },

  // Next's compression middleware matches `text/*`, so it gzips the
  // `text/event-stream` response produced by the `/api/backend` rewrite.
  // gzip buffers, which defeats SSE: the dev server flushed the whole AI
  // research stream as a single ~31 KB chunk ~29 s in, and on longer RAG
  // answers the stalled connection was reset, surfacing in the browser as
  // `ERR_INCOMPLETE_CHUNKED_ENCODING` / "Generation failed".
  //
  // Compression is therefore disabled in development only, where on-the-fly
  // compilation makes the buffering stall long enough to trip the failure.
  // Production keeps compression exactly as before, so nothing about the
  // deployed app changes.
  compress: process.env.NODE_ENV === "production",

  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
