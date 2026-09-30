import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
