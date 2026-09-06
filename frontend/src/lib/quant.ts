/**
 * Small numeric helpers used by the charts and by the bundled MOCK
 * generator. Everything here is deterministic and dependency-free.
 *
 * The CRPS estimators follow the forms verified in Phase-1 recon:
 *  - ensemble CRPS uses the FAIR (unbiased) estimator, pairwise term
 *    divided by 2m(m-1), evaluated via the O(m log m) sorted identity
 *    sum_i sum_j |x_i - x_j| = 2 * sum_i (2i - m - 1) * x_(i).
 *  - the Gaussian null uses the CLOSED FORM, not a sample, so that
 *    lift is not distorted by estimator asymmetry.
 * The backend (LANE-EVAL) owns the scores that matter; these exist so
 * the MOCK mode is internally consistent rather than hand-typed.
 */

import type { PathsPayload, Quantiles } from "./types";

/* ---------- deterministic RNG (mulberry32) ---------- */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function seedFrom(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Box-Muller standard normal from a uniform source. */
export function gauss(u: () => number): number {
  let a = u();
  if (a < 1e-12) a = 1e-12;
  return Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * u());
}

/* ---------- distribution utilities ---------- */
export function quantileSorted(sorted: number[], q: number): number {
  if (sorted.length === 0) return NaN;
  if (sorted.length === 1) return sorted[0];
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  if (lo === hi) return sorted[lo];
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

export function quantilesOf(values: number[]): Quantiles {
  const s = [...values].sort((a, b) => a - b);
  return {
    p5: quantileSorted(s, 0.05),
    p25: quantileSorted(s, 0.25),
    p50: quantileSorted(s, 0.5),
    p75: quantileSorted(s, 0.75),
    p95: quantileSorted(s, 0.95),
  };
}

export function meanOf(v: number[]): number {
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : 0;
}

export function stdOf(v: number[]): number {
  if (v.length < 2) return 0;
  const m = meanOf(v);
  return Math.sqrt(v.reduce((a, b) => a + (b - m) * (b - m), 0) / (v.length - 1));
}

export interface Bin { x0: number; x1: number; n: number }

export function histogram(values: number[], nbins: number, lo?: number, hi?: number): Bin[] {
  if (values.length === 0) return [];
  const min = lo ?? Math.min(...values);
  const max = hi ?? Math.max(...values);
  const span = max - min || 1;
  const bins: Bin[] = Array.from({ length: nbins }, (_, i) => ({
    x0: min + (span * i) / nbins,
    x1: min + (span * (i + 1)) / nbins,
    n: 0,
  }));
  for (const v of values) {
    let k = Math.floor(((v - min) / span) * nbins);
    if (k < 0) k = 0;
    if (k >= nbins) k = nbins - 1;
    bins[k].n += 1;
  }
  return bins;
}

/* ---------- normal CDF / PDF ---------- */
export function erf(x: number): number {
  // Abramowitz & Stegun 7.1.26, |eps| < 1.5e-7
  const sign = x < 0 ? -1 : 1;
  const z = Math.abs(x);
  const t = 1 / (1 + 0.3275911 * z);
  const y =
    1 -
    ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t +
      0.254829592) *
      t *
      Math.exp(-z * z);
  return sign * y;
}
export const Phi = (z: number) => 0.5 * (1 + erf(z / Math.SQRT2));
export const phi = (z: number) => Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);

/* ---------- scoring ---------- */

/** Fair (unbiased) ensemble CRPS, O(m log m). Lower is better. */
export function crpsEnsembleFair(sample: number[], y: number): number {
  const m = sample.length;
  if (m === 0) return NaN;
  if (m === 1) return Math.abs(sample[0] - y);
  const s = [...sample].sort((a, b) => a - b);
  let term1 = 0;
  let pair = 0;
  for (let i = 0; i < m; i++) {
    term1 += Math.abs(s[i] - y);
    pair += (2 * (i + 1) - m - 1) * s[i]; // sorted identity
  }
  return term1 / m - pair / (m * (m - 1));
}

/** Closed-form CRPS for N(mu, sigma) at y. */
export function crpsGaussian(mu: number, sigma: number, y: number): number {
  if (!(sigma > 0)) return Math.abs(y - mu);
  const z = (y - mu) / sigma;
  return sigma * (z * (2 * Phi(z) - 1) + 2 * phi(z) - 1 / Math.sqrt(Math.PI));
}

/** Randomized PIT (flat at any ensemble size) — recon's recommendation. */
export function pitRandomized(sample: number[], y: number, u: number): number {
  const m = sample.length;
  if (m === 0) return NaN;
  let below = 0;
  for (const x of sample) if (x < y) below++;
  return (below + u) / (m + 1);
}

/* ---------- shape handling for Ensemble.paths ---------- */
export function isPathMatrix(p: PathsPayload): p is number[][] {
  return Array.isArray(p) && p.length > 0 && Array.isArray(p[0]);
}

/** Terminal cumulative returns, whichever shape the backend sent. */
export function terminalReturns(p: PathsPayload): number[] {
  if (!Array.isArray(p) || p.length === 0) return [];
  if (isPathMatrix(p)) return p.map((row) => (row.length ? row[row.length - 1] : 0));
  return (p as number[]).filter((x) => typeof x === "number" && Number.isFinite(x));
}

export interface FanBand {
  /** one entry per step, step 0 = as_of (return 0) */
  p5: number[]; p25: number[]; p50: number[]; p75: number[]; p95: number[];
  steps: number;
  /** true when we only had terminal returns and expanded them by sqrt(t) */
  interpolated: boolean;
}

/**
 * Build the fan.
 * If the backend gave a full path matrix we take honest per-step quantiles.
 * If it gave terminal returns only (the literal CONTRACT reading) we expand
 * the terminal quantiles backwards by sqrt(t/T) — a diffusive envelope — and
 * flag it as interpolated ON SCREEN so nobody mistakes it for path data.
 */
export function buildFan(paths: PathsPayload, horizon: number): FanBand {
  if (isPathMatrix(paths)) {
    const steps = Math.max(...paths.map((r) => r.length));
    const out: FanBand = { p5: [0], p25: [0], p50: [0], p75: [0], p95: [0], steps, interpolated: false };
    for (let t = 0; t < steps; t++) {
      const col = paths.map((r) => (t < r.length ? r[t] : r[r.length - 1]));
      const q = quantilesOf(col);
      out.p5.push(q.p5); out.p25.push(q.p25); out.p50.push(q.p50);
      out.p75.push(q.p75); out.p95.push(q.p95);
    }
    out.steps = steps;
    return out;
  }
  const term = terminalReturns(paths);
  const q = quantilesOf(term);
  const H = Math.max(1, horizon);
  const band: FanBand = { p5: [], p25: [], p50: [], p75: [], p95: [], steps: H, interpolated: true };
  for (let t = 0; t <= H; t++) {
    const s = Math.sqrt(t / H);
    band.p5.push(q.p5 * s);
    band.p25.push(q.p25 * s);
    band.p50.push(q.p50 * s);
    band.p75.push(q.p75 * s);
    band.p95.push(q.p95 * s);
  }
  return band;
}

/* ---------- formatting ---------- */
export const pct = (x: number, d = 1) =>
  `${x >= 0 ? "+" : "−"}${(Math.abs(x) * 100).toFixed(d)}%`;
export const pctPlain = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;
export const fixed = (x: number, d = 4) =>
  Number.isFinite(x) ? x.toFixed(d) : "—";
