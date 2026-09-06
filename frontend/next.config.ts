import type { NextConfig } from "next";

/**
 * Dev: proxy /api/* to the FastAPI backend on :8000 (CONTRACT.md §6).
 * Deployed: set NEXT_PUBLIC_API_BASE to the backend origin instead and the
 * client calls it directly (see src/lib/api.ts).
 */
const BACKEND = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

const STATIC = process.env.STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  // Cloudflare Pages: fully prerendered, no Node server. Rewrites are disabled
  // in this mode, so the client must call the backend via NEXT_PUBLIC_API_BASE
  // (or run in mock mode, which needs no backend at all).
  ...(STATIC ? { output: "export" as const, images: { unoptimized: true } } : {}),
  // package-lock.json can exist above the repo on a dev machine; pin the root
  // so Turbopack never resolves outside frontend/.
  turbopack: { root: process.cwd() },

  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_BASE) return [];
    return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }];
  },
};

export default nextConfig;
