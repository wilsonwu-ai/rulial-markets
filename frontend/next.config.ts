import type { NextConfig } from "next";

/**
 * Two deploy shapes, one config.
 *
 * 1. Local / Node host (default)
 *    `next dev` or `next start` on :3000, proxying /api/* to the FastAPI
 *    backend on :8000 per CONTRACT.md §6.
 *
 * 2. Static export (Cloudflare Pages and any other flat-file CDN)
 *    Every route here is fully prerenderable — all data fetching happens in
 *    the browser — so the frontend ships as plain files:
 *
 *      NEXT_PUBLIC_API_BASE=https://<backend-origin> STATIC_EXPORT=1 npm run build
 *
 *    writes `out/`. An export has no rewrite layer, so the API origin must be
 *    baked in at build time; we fail loudly rather than shipping a bundle that
 *    calls a /api which isn't there. (The UI still works with no backend at
 *    all — it falls back to bundled mock mode — but that should be a choice,
 *    not an accident of a missing env var.)
 */
const STATIC = process.env.STATIC_EXPORT === "1";
const BACKEND = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

if (STATIC && !process.env.NEXT_PUBLIC_API_BASE) {
  throw new Error(
    "STATIC_EXPORT=1 requires NEXT_PUBLIC_API_BASE — a static export has no /api proxy.",
  );
}

const nextConfig: NextConfig = {
  ...(STATIC ? { output: "export" as const, images: { unoptimized: true } } : {}),

  // package-lock.json can sit above the repo on a dev machine; pin the root so
  // Turbopack never resolves outside frontend/.
  turbopack: { root: process.cwd() },

  async rewrites() {
    // No proxy needed when the client has an absolute API base, and rewrites
    // are meaningless in an export.
    if (STATIC || process.env.NEXT_PUBLIC_API_BASE) return [];
    return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }];
  },
};

export default nextConfig;
