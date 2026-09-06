/**
 * THE ATLAS — real weekly closes plus every detected event, bundled.
 *
 * `public/data/atlas.json` is built once, offline, from real price history and
 * researched causes. It is NOT model output and it is NOT mode-dependent: the
 * live / precomputed / mock switch governs the FORECAST surfaces only. The
 * atlas is the same real bundle in all three, and every panel that renders it
 * says so on its own face rather than inheriting a page-level badge.
 *
 * Shape, verified against the shipped file (329 events, 10 tickers,
 * BA and XOM back to 1962):
 *
 *   { generated: string,
 *     tickers: { AAPL: { series: [[iso, close], ...],
 *                        events: [AtlasEvent, ...],
 *                        first, last, n_events } } }
 *
 * 233 of the 329 events carry a researched headline, cause, category and up to
 * three source URLs. The other 96 do not, and the UI must render that absence
 * as a fact rather than papering it over — see `isExplained`.
 */

export interface AtlasEvent {
  date: string;
  /** close-to-close return over the frozen 5-session window, e.g. -0.1943 */
  move: number;
  dir: "up" | "down";
  /** CONTRACT §3 two-tier definition */
  tier: "major" | "significant";
  famous: boolean;
  headline?: string;
  cause?: string;
  category?: string;
  sources?: string[];
  confidence?: number;
}

export interface AtlasTicker {
  /** [ISO date, close] weekly, ascending */
  series: [string, number][];
  events: AtlasEvent[];
  first: string;
  last: string;
  n_events: number;
}

export interface Atlas {
  generated: string;
  tickers: Record<string, AtlasTicker>;
}

export const ATLAS_NOTICE =
  "Real weekly closes and 329 detected events, bundled with the build. Not model output, " +
  "and not affected by the live / precomputed / mock switch.";

/** An event we can explain. 96 of the 329 we cannot, and we say so. */
export function isExplained(e: AtlasEvent): boolean {
  return Boolean(e.headline && e.headline.trim());
}

/** Stable identity for selection state. */
export function eventKey(ticker: string, e: AtlasEvent): string {
  return `${ticker}|${e.date}`;
}

/* ---------------------------------------------------------------- loading */

let _atlas: Atlas | null = null;
let _inflight: Promise<Atlas | null> | null = null;

export async function loadAtlas(): Promise<Atlas | null> {
  if (_atlas) return _atlas;
  if (_inflight) return _inflight;
  _inflight = (async () => {
    try {
      const res = await fetch("/data/atlas.json", { cache: "force-cache" });
      if (!res.ok) return null;
      const json = (await res.json()) as Atlas;
      if (!json?.tickers) return null;
      _atlas = json;
      return json;
    } catch {
      return null;
    } finally {
      _inflight = null;
    }
  })();
  return _inflight;
}

/* ------------------------------------------------------------------ time */

export const DAY_MS = 86_400_000;

/** ISO date -> epoch ms at UTC midnight. Parsed by hand rather than by Date
 *  so a "1962-01-02" never drifts a day under a negative local offset. */
export function toMs(iso: string): number {
  const y = Number(iso.slice(0, 4));
  const m = Number(iso.slice(5, 7));
  const d = Number(iso.slice(8, 10));
  return Date.UTC(y, m - 1, d);
}

export function toIso(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

export function yearOf(ms: number): number {
  return new Date(ms).getUTCFullYear();
}

/** Trading days -> calendar days. 5 sessions is a week of the wall clock, and
 *  the branch chart draws on a calendar axis, so the horizon has to be
 *  converted rather than assumed. */
export function tradingToCalendarDays(tradingDays: number): number {
  return Math.max(1, Math.round((tradingDays * 7) / 5));
}

export interface Span { lo: number; hi: number }

/** Full time domain covered by the atlas, across every ticker. */
export function atlasDomain(atlas: Atlas): Span {
  let lo = Infinity;
  let hi = -Infinity;
  for (const t of Object.values(atlas.tickers)) {
    if (t.first) lo = Math.min(lo, toMs(t.first));
    if (t.last) hi = Math.max(hi, toMs(t.last));
  }
  if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) {
    return { lo: toMs("1962-01-01"), hi: toMs("2026-12-31") };
  }
  return { lo, hi };
}

/** Clamp a candidate view to the domain, keeping its width where possible. */
export function clampSpan(view: Span, domain: Span, minDays = 60): Span {
  const minSpan = minDays * DAY_MS;
  const full = domain.hi - domain.lo;
  let width = Math.min(Math.max(view.hi - view.lo, minSpan), full);
  if (!Number.isFinite(width) || width <= 0) width = full;
  let lo = view.lo;
  if (lo < domain.lo) lo = domain.lo;
  if (lo + width > domain.hi) lo = domain.hi - width;
  return { lo, hi: lo + width };
}

/* ---------------------------------------------------------------- series */

/**
 * Points inside [lo, hi] plus one on each side, so a line entering and leaving
 * the viewport is drawn to the edge instead of stopping short of it.
 * Binary search: the longest series is 3,256 points and this runs on every
 * pan frame for ten of them at once.
 */
export function sliceSeries(
  series: [string, number][],
  lo: number,
  hi: number,
): { ms: number; v: number }[] {
  if (!series.length) return [];
  const at = (i: number) => toMs(series[i][0]);

  let a = 0;
  let b = series.length - 1;
  while (a < b) {
    const mid = (a + b) >> 1;
    if (at(mid) < lo) a = mid + 1;
    else b = mid;
  }
  const start = Math.max(0, a - 1);

  a = start;
  b = series.length - 1;
  while (a < b) {
    const mid = (a + b + 1) >> 1;
    if (at(mid) <= hi) a = mid;
    else b = mid - 1;
  }
  const end = Math.min(series.length - 1, a + 1);

  const out: { ms: number; v: number }[] = [];
  for (let i = start; i <= end; i++) {
    const v = series[i][1];
    if (typeof v === "number" && Number.isFinite(v) && v > 0) {
      out.push({ ms: at(i), v });
    }
  }
  return out;
}

/** Last close on or before `ms`, or the first close if `ms` predates the series. */
export function closeAt(series: [string, number][], ms: number): number | null {
  if (!series.length) return null;
  let a = 0;
  let b = series.length - 1;
  if (toMs(series[0][0]) > ms) return series[0][1];
  while (a < b) {
    const mid = (a + b + 1) >> 1;
    if (toMs(series[mid][0]) <= ms) a = mid;
    else b = mid - 1;
  }
  const v = series[a][1];
  return Number.isFinite(v) && v > 0 ? v : null;
}

/** Every point strictly after `ms` and up to `ms + spanMs`. Used for the
 *  "what came next" tail on the branch chart, which is REAL price data drawn
 *  past the model horizon and labelled as such. */
export function seriesAfter(
  series: [string, number][],
  ms: number,
  spanMs: number,
): { ms: number; v: number }[] {
  return sliceSeries(series, ms, ms + spanMs).filter((p) => p.ms > ms);
}

/* ---------------------------------------------------------------- events */

export interface FlatEvent extends AtlasEvent {
  ticker: string;
  key: string;
}

export function flattenEvents(atlas: Atlas, tickers?: string[]): FlatEvent[] {
  const out: FlatEvent[] = [];
  for (const [sym, t] of Object.entries(atlas.tickers)) {
    if (tickers && !tickers.includes(sym)) continue;
    for (const e of t.events) out.push({ ...e, ticker: sym, key: eventKey(sym, e) });
  }
  out.sort((a, b) => toMs(a.date) - toMs(b.date));
  return out;
}

/** Marker radius from magnitude. 15% (the detection floor) is the smallest
 *  mark; 50%+ saturates. Never below 3.5px — a 2px dot on a projector is
 *  indistinguishable from dust. */
export function markerRadius(move: number): number {
  const m = Math.abs(move);
  const t = Math.min(1, Math.max(0, (m - 0.15) / 0.35));
  return 3.5 + t * 7;
}

/** Human label for a category, or the honest absence. */
export function categoryLabel(c?: string): string {
  if (!c) return "uncategorised";
  return c.replace(/-/g, " ");
}

export const CATEGORY_ORDER = [
  "macro", "earnings", "guidance", "crisis", "geopolitical",
  "regulatory", "sector-rotation", "product", "leadership",
  "sentiment", "unexplained",
] as const;
