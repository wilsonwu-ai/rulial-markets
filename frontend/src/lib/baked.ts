/**
 * PRECOMPUTED data source — real forward-model output, baked at build time.
 *
 * This exists because of a genuine failure mode. The venue network blocks
 * cloudflared's port 7844, so there is no tunnel and no hosted backend. Without
 * this module the deployed app probed :8000, got nothing, and fell straight
 * through to `mock.ts` — in-browser seeded RNG — while 22 files of REAL
 * generator output sat unread in public/data/.
 *
 * Showing synthetic numbers on a project whose entire thesis is not fabricating
 * numbers is the worst possible demo failure, so precomputed sits ABOVE mock in
 * the fallback order:
 *
 *     live  ->  baked (real, precomputed)  ->  mock (synthetic, last resort)
 *
 * Everything here was produced by generator.generate_ensemble over real price
 * history and scored by evaluate.py. It is stale rather than fake: pinned to the
 * corpus at build time, not made up in the browser.
 */
import type {
  Backtest, EventRec, ForecastRequest, ForecastResponse, TickerInfo,
} from "./types";

export const BAKED_NOTICE =
  "PRECOMPUTED — real forward-model output computed from real price history at build time, " +
  "not synthetic. The live backend is not reachable from this network, so these are stored " +
  "results rather than fresh ones.";

export interface BakedForecastMeta {
  key: string; file: string; ticker: string; as_of: string;
  horizon_days: number; label: string; note: string; superseded: boolean;
  crps_lift: number | null; z_score: number | null;
  actual: number | null; pit: number | null;
}

interface BakedIndex { generated: string; kind: string; note: string; forecasts: BakedForecastMeta[] }

let _index: BakedIndex | null = null;
let _indexTried = false;

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(path, { cache: "force-cache" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function bakedIndex(): Promise<BakedIndex | null> {
  if (_indexTried) return _index;
  _indexTried = true;
  _index = await getJson<BakedIndex>("/data/index.json");
  return _index;
}

/** True when the precomputed bundle shipped with this build. */
export async function bakedAvailable(): Promise<boolean> {
  const i = await bakedIndex();
  return !!(i && Array.isArray(i.forecasts) && i.forecasts.length > 0);
}

/** Scenarios worth putting on screen: the superseded first-pass ones are hidden. */
export async function bakedScenarios(): Promise<BakedForecastMeta[]> {
  const i = await bakedIndex();
  return (i?.forecasts ?? []).filter((f) => !f.superseded);
}

export async function bakedTickers(): Promise<TickerInfo[] | null> {
  return getJson<TickerInfo[]>("/data/tickers.json");
}

export async function bakedEvents(ticker: string): Promise<EventRec[] | null> {
  return getJson<EventRec[]>(`/data/events_${encodeURIComponent(ticker.toUpperCase())}.json`);
}

export async function bakedBacktest(ticker: string): Promise<Backtest | null> {
  return getJson<Backtest>(`/data/backtest_${encodeURIComponent(ticker.toUpperCase())}.json`);
}

/** Cheap bag-of-words overlap, only used to break ties between two baked runs
 *  that share a ticker and date and differ solely in their event text (the
 *  paired control). */
function overlap(a: string, b: string): number {
  const tok = (s: string) =>
    new Set(s.toLowerCase().replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter((w) => w.length > 3));
  const A = tok(a), B = tok(b);
  if (!A.size || !B.size) return 0;
  let hit = 0;
  A.forEach((w) => { if (B.has(w)) hit += 1; });
  return hit / Math.min(A.size, B.size);
}

/**
 * Best precomputed match for a request, or null.
 * Matches on ticker plus as-of date; when several share both, the event text
 * decides. Returns null rather than a poor match, so the caller can fall
 * through to mock instead of silently showing the wrong scenario.
 */
export async function bakedForecast(req: ForecastRequest): Promise<ForecastResponse | null> {
  const all = await bakedScenarios();
  const cands = all.filter(
    (f) => f.ticker === req.ticker.toUpperCase() && f.as_of === req.as_of_date,
  );
  if (!cands.length) return null;

  let best = cands[0];
  if (cands.length > 1) {
    let bestScore = -1;
    for (const c of cands) {
      const doc = await getJson<ForecastResponse>(c.file);
      const narrative = doc?.ensemble?.narrative ?? "";
      const s = overlap(req.event_text ?? "", `${c.label} ${c.note} ${narrative}`);
      if (s > bestScore) { bestScore = s; best = c; }
    }
  }
  const doc = await getJson<ForecastResponse>(best.file);
  if (!doc) return null;
  // ForecastResponse carries no notes field; provenance is surfaced by the
  // banner in Console.tsx and by bakedMatchLabel below, so the payload stays
  // exactly the shape the live API returns.
  return doc;
}

/** Human label for whichever precomputed scenario answered a request. */
export async function bakedMatchLabel(req: ForecastRequest): Promise<string | null> {
  const cands = (await bakedScenarios()).filter(
    (f) => f.ticker === req.ticker.toUpperCase() && f.as_of === req.as_of_date,
  );
  return cands.length ? `${cands[0].label} (${cands[0].note})` : null;
}
