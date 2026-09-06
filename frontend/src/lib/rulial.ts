/**
 * ============================================================
 *  RULIAL ENSEMBLE CLIENT — CONTRACT.md §6d
 * ============================================================
 * A Boltzmann ensemble varies the CONFIGURATION under one fixed rule. Its
 * spread answers "how uncertain is the outcome, given my model is right?".
 * A rulial ensemble varies the RULE. Its spread answers "how uncertain am I,
 * given I do not know which rule generates reality?".
 *
 * We ship both. Dropping Boltzmann would hide the comparison that justifies
 * the whole construction, so it stays in the response and stays on screen.
 *
 * ------------------------------------------------------------------
 * FROZEN, and these are exactly the rules an optimizer would break:
 *
 *   1. The grid is 144 and FIXED — 4 x 3 x 4 x 3. No axis may be pruned,
 *      reweighted or extended. `EXPECTED_GENERATORS` below is computed from
 *      RULE_AXES rather than typed, so an edit to an axis is impossible to
 *      make quietly: the count on screen moves with it.
 *   2. `reducible` and every agreement fraction are MEASURED from the
 *      returned per-generator distributions. Nothing in this file can assert
 *      an agreement number — `measureProperties` only counts.
 *   3. A property that flips across the grid is returned in the
 *      RULE-DEPENDENT list and carries its measured agreement with it. The
 *      renderer has no code path that prints one of those as a finding.
 *
 * ------------------------------------------------------------------
 * THREE SOURCES, in the same order as the rest of the app (see baked.ts):
 *
 *     live  ->  baked (real, precomputed)  ->  mock (synthetic, last resort)
 *
 * `bakedRulial` looks for /data/rulial_<TICKER>_<AS_OF>.json, the same flat
 * per-key convention `bakedBacktest` uses for /data/backtest_<TICKER>.json.
 * A miss returns null and the caller falls through to the synthetic path
 * rather than answering with a run the user did not ask for.
 * ------------------------------------------------------------------
 */

import type { Mode, Quantiles } from "./types";
import { gauss, meanOf, quantilesOf, rng, seedFrom, stdOf } from "./quant";
import { mockForecast } from "./mock";

/* ================================================================
   THE FROZEN GRID — CONTRACT §6d, verbatim
   ================================================================ */

export const RULE_AXES = {
  analog_selection: ["tfidf_magnitude", "ticker_only", "tier_only", "text_only"], // 4
  conditioning: ["cross_ticker", "same_ticker", "same_era"], //                      3
  drift_prior: ["scenario", "zero", "unconditional", "sign_only"], //                4
  resampling: ["block", "iid", "stationary"], //                                     3
} as const;

export type AxisName = keyof typeof RULE_AXES;

/** Declaration order is the display order everywhere in the UI. */
export const AXIS_ORDER: AxisName[] = [
  "analog_selection", "conditioning", "drift_prior", "resampling",
];

/** Short prefix per axis. Used to build the CSS highlight keys (a0, c1, d2, r0)
 *  that let the chart dim 144 SVG paths without a React re-render. */
export const AXIS_KEY: Record<AxisName, string> = {
  analog_selection: "a", conditioning: "c", drift_prior: "d", resampling: "r",
};

export const AXIS_LABEL: Record<AxisName, string> = {
  analog_selection: "analog selection",
  conditioning: "conditioning",
  drift_prior: "drift prior",
  resampling: "resampling",
};

/** 4 * 3 * 4 * 3 = 144. COMPUTED from the axes, never typed as a literal —
 *  so no edit to RULE_AXES can leave a stale 144 on screen. */
export const EXPECTED_GENERATORS = AXIS_ORDER.reduce(
  (n, a) => n * RULE_AXES[a].length, 1,
);

export interface Rule {
  analog_selection: string;
  conditioning: string;
  drift_prior: string;
  resampling: string;
  [k: string]: string;
}

/** Every point of the frozen grid, in a stable order. */
export function ruleGrid(): Rule[] {
  const out: Rule[] = [];
  for (const a of RULE_AXES.analog_selection)
    for (const c of RULE_AXES.conditioning)
      for (const d of RULE_AXES.drift_prior)
        for (const r of RULE_AXES.resampling)
          out.push({ analog_selection: a, conditioning: c, drift_prior: d, resampling: r });
  return out;
}

/** CSS highlight key for one rule on one axis, e.g. drift_prior=zero -> "d1". */
export function levelKey(axis: AxisName, level: string): string {
  const i = (RULE_AXES[axis] as readonly string[]).indexOf(level);
  return `${AXIS_KEY[axis]}${i}`;
}

/* ================================================================
   WIRE TYPES — CONTRACT §6d
   Optional fields are extras a backend lane MAY add (same convention as
   types.ts). The UI renders them when present and never requires them.
   ================================================================ */

export interface RulialRequest {
  ticker: string;
  event_text: string;
  as_of_date: string;
  horizon_days?: number;
  n_paths_per_rule?: number;
}

export interface BoltzmannLeg {
  quantiles: Quantiles;
  median: number;
  p_down: number;
  n_paths: number;
}

export interface GeneratorResult {
  rule: Rule;
  quantiles: Quantiles;
  median: number;
  p_down: number;
  /** optional extra: a rule that raised is reported, never dropped */
  failed?: boolean;
  error?: string;
}

export interface Consensus {
  median_band: [number, number];
  p_down_band: [number, number];
  sign_agreement: number;
  reducible: boolean;
}

export interface RulialLeg {
  n_generators: number;
  per_generator: GeneratorResult[];
  consensus: Consensus;
  /** optional extra: rules that raised rather than returning */
  n_failed?: number;
}

export interface RulialResponse {
  boltzmann: BoltzmannLeg;
  rulial: RulialLeg;
  invariants: string[];
  rule_dependent: string[];
  note: string;
  /** Set by this client, not by the wire: which engine produced the numbers. */
  source?: Mode;
}

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const TIMEOUT_MS = 45000;

export class RulialError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "RulialError";
  }
}

/* ================================================================
   SOURCE 1 — LIVE
   ================================================================ */

async function liveRulial(body: RulialRequest): Promise<RulialResponse> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE}/api/rulial`, {
      method: "POST",
      signal: ctrl.signal,
      cache: "no-store",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const t = await res.text().catch(() => "");
      throw new RulialError(
        `${res.status} ${res.statusText}${t ? ` — ${t.slice(0, 180)}` : ""}`,
        res.status,
      );
    }
    const json = (await res.json()) as RulialResponse;
    return { ...json, source: "live" };
  } catch (e) {
    if (e instanceof RulialError) throw e;
    const msg = e instanceof Error ? e.message : String(e);
    throw new RulialError(
      msg.includes("abort") ? `backend did not answer in ${TIMEOUT_MS / 1000}s` : msg,
    );
  } finally {
    clearTimeout(timer);
  }
}

/* ================================================================
   SOURCE 2 — BAKED (real output precomputed at build time)
   ================================================================ */

/** Filename convention for a precomputed rulial run. Documented here so the
 *  bundle can be generated without reading this file. */
export function bakedRulialPath(ticker: string, asOf: string): string {
  return `/data/rulial_${encodeURIComponent(ticker.toUpperCase())}_${asOf}.json`;
}

export async function bakedRulial(req: RulialRequest): Promise<RulialResponse | null> {
  try {
    const res = await fetch(bakedRulialPath(req.ticker, req.as_of_date), {
      cache: "force-cache",
    });
    if (!res.ok) return null;
    const json = (await res.json()) as RulialResponse;
    if (!json?.rulial?.per_generator?.length) return null;
    return { ...json, source: "baked" };
  } catch {
    return null;
  }
}

/* ================================================================
   THE THREE-SOURCE ENTRY POINT
   Same order and same failure semantics as api.ts: a LIVE failure is thrown
   rather than silently mocked, so the panel can surface it and offer the
   synthetic path explicitly instead of pretending a dead backend answered.
   ================================================================ */

export async function requestRulial(
  mode: Mode,
  body: RulialRequest,
): Promise<RulialResponse> {
  if (mode === "mock") {
    return new Promise((r) => setTimeout(() => r(mockRulial(body)), 380));
  }
  if (mode === "baked") {
    const doc = await bakedRulial(body);
    if (doc) return doc;
    return new Promise((r) => setTimeout(() => r(mockRulial(body)), 380));
  }
  return liveRulial(body);
}

/* ================================================================
   SOURCE 3 — MOCK. SYNTHETIC. NOT MARKET DATA, NOT MODEL OUTPUT.
   ================================================================
 * This WRAPS the existing single-rule mock generator exactly as the backend
 * rulial engine wraps `generator.generate_ensemble`: `mockForecast` produces
 * the Boltzmann leg, and each of the 144 rules is a perturbation of that one
 * base ensemble. It does not reimplement the forward model.
 *
 * Two honesty properties hold here as they do in live mode:
 *
 *   - every quantile, median, p_down, agreement fraction and `reducible`
 *     verdict is MEASURED from the sampled paths. Nothing is written in.
 *   - no axis is skipped. All 144 points of the grid are sampled even where
 *     the perturbation is small, because a grid you prune is not a grid.
 *
 * SAID OUT LOUD, because it matters: the DRIFT axis dominates the spread in
 * this synthetic world BY CONSTRUCTION — the four drift levels are literally
 * four different location parameters. That mirrors what the real measurement
 * showed (a +14.8% CRPS lift that becomes -4.5% once demeaned is a drift-axis
 * rule-dependence), but seeing it here is NOT evidence for it. It is a mock
 * shaped like the finding so the surface can be demonstrated with the backend
 * down. The panel says SYNTHETIC on screen whenever this path runs.
 */

const MOCK_NOTE =
  "SYNTHETIC — this rulial ensemble was generated in-browser by a seeded RNG wrapping the " +
  "bundled mock forward model, because neither the live backend nor a precomputed bundle " +
  "answered. Every agreement fraction below is still MEASURED from the 144 sampled " +
  "distributions rather than asserted, but the distributions themselves are not market data " +
  "and the drift-axis dominance is built into the mock rather than discovered by it.";

/** Per-axis multipliers on (drift, sigma). Deliberately explicit rather than
 *  generated, so what each axis does to the answer is readable. */
const ANALOG_EFFECT: Record<string, [number, number]> = {
  tfidf_magnitude: [1.00, 1.00],
  ticker_only: [0.86, 0.94],
  tier_only: [1.12, 1.09],
  text_only: [0.94, 1.03],
};
const COND_EFFECT: Record<string, [number, number]> = {
  cross_ticker: [0.80, 1.14],
  same_ticker: [1.10, 0.90],
  same_era: [1.00, 1.02],
};
/** sigma multiplier + weight of a fat-tailed dislocation branch */
const RESAMPLE_EFFECT: Record<string, [number, number]> = {
  block: [1.06, 0.14],
  iid: [1.00, 0.00],
  stationary: [1.03, 0.07],
};

/** The drift axis is the one that moves the answer. `scenario` keeps the
 *  event-conditioned location, `zero` throws it away, `unconditional` replaces
 *  it with a flat historical drift that ignores the event entirely, and
 *  `sign_only` keeps the direction but discards the magnitude. */
function driftFor(level: string, baseMu: number, horizon: number): number {
  switch (level) {
    case "scenario": return baseMu;
    case "zero": return 0;
    case "unconditional": return 0.0003 * horizon;
    case "sign_only": return Math.sign(baseMu) * Math.abs(baseMu) * 0.35;
    default: return baseMu;
  }
}

function pDownOf(sample: number[]): number {
  if (!sample.length) return NaN;
  let n = 0;
  for (const x of sample) if (x < 0) n += 1;
  return n / sample.length;
}

export function mockRulial(req: RulialRequest): RulialResponse {
  const H = req.horizon_days ?? 5;
  const nPer = Math.max(80, Math.min(req.n_paths_per_rule ?? 400, 1200));

  /* ---- Boltzmann leg: the EXISTING single-rule mock, unmodified ---- */
  const base = mockForecast({
    ticker: req.ticker,
    event_text: req.event_text,
    as_of_date: req.as_of_date,
    horizon_days: H,
    n_paths: 2000,
  });
  const basePaths = Array.isArray(base.ensemble.paths)
    ? (base.ensemble.paths as number[]).filter((x) => typeof x === "number" && Number.isFinite(x))
    : [];
  const bq = quantilesOf(basePaths);
  const boltzmann: BoltzmannLeg = {
    quantiles: bq,
    median: bq.p50,
    p_down: pDownOf(basePaths),
    n_paths: basePaths.length,
  };

  const baseMu = meanOf(basePaths);
  const baseSd = stdOf(basePaths);

  /* ---- rulial leg: all 144 points of the frozen grid ---- */
  const per: GeneratorResult[] = [];
  for (const rule of ruleGrid()) {
    const key = `${req.ticker}|${req.as_of_date}|${req.event_text}|${H}|` +
      `${rule.analog_selection}|${rule.conditioning}|${rule.drift_prior}|${rule.resampling}`;
    const r = rng(seedFrom(key));

    const [aD, aS] = ANALOG_EFFECT[rule.analog_selection] ?? [1, 1];
    const [cD, cS] = COND_EFFECT[rule.conditioning] ?? [1, 1];
    const [sS, tailW] = RESAMPLE_EFFECT[rule.resampling] ?? [1, 0];

    // Small deterministic jitter so two rules sharing three axes are not
    // pixel-identical. Bounded well below the axis effects themselves.
    const jD = 1 + 0.06 * (r() - 0.5) * 2;
    const jS = 1 + 0.05 * (r() - 0.5) * 2;

    const mu = driftFor(rule.drift_prior, baseMu, H) * aD * cD * jD;
    const sd = baseSd * aS * cS * sS * jS;

    const sample: number[] = new Array(nPer);
    for (let i = 0; i < nPer; i++) {
      const fat = tailW > 0 && r() < tailW;
      sample[i] = mu + (fat ? sd * 1.7 : sd) * gauss(r);
    }

    const q = quantilesOf(sample);
    per.push({ rule, quantiles: q, median: q.p50, p_down: pDownOf(sample) });
  }

  /* ---- consensus: MEASURED, every field ---- */
  const meds = per.map((g) => g.median);
  const pdowns = per.map((g) => g.p_down);
  const nNeg = meds.filter((m) => m < 0).length;
  const modal = Math.max(nNeg, meds.length - nNeg);
  const signAgreement = meds.length ? modal / meds.length : 0;

  const consensus: Consensus = {
    median_band: [Math.min(...meds), Math.max(...meds)],
    p_down_band: [Math.min(...pdowns), Math.max(...pdowns)],
    sign_agreement: signAgreement,
    // MEASURED against the frozen 90% threshold, not asserted.
    reducible: signAgreement >= INVARIANT_THRESHOLD,
  };

  const props = measureProperties(per, boltzmann);

  return {
    boltzmann,
    rulial: { n_generators: per.length, per_generator: per, consensus, n_failed: 0 },
    invariants: props.filter((p) => p.invariant).map(propSentence),
    rule_dependent: props.filter((p) => !p.invariant).map(propSentence),
    note: MOCK_NOTE,
    source: "mock",
  };
}

/* ================================================================
   MEASUREMENT HELPERS — used for BOTH live and mock responses.
   These read the returned per-generator distributions and count. There is no
   argument here that can be passed to make a number larger.
   ================================================================ */

/** CONTRACT §6d: a property is INVARIANT when it holds under >= 90% of the grid. */
export const INVARIANT_THRESHOLD = 0.9;

export interface PropertyAgreement {
  /** stated in whichever polarity the majority of rules support */
  statement: string;
  /** fraction of the 144 under which the STATEMENT holds. Always >= 0.5. */
  agreement: number;
  invariant: boolean;
  /** what the minority does instead — kept so the flip is nameable */
  counter: string;
}

function propSentence(p: PropertyAgreement): string {
  return `${p.statement} (${(p.agreement * 100).toFixed(0)}% of rules)`;
}

function agreementOf(
  per: GeneratorResult[],
  positive: string,
  negative: string,
  test: (g: GeneratorResult) => boolean,
): PropertyAgreement {
  const n = per.length;
  const hits = per.filter(test).length;
  const frac = n ? hits / n : 0;
  const majority = frac >= 0.5;
  const agreement = majority ? frac : 1 - frac;
  return {
    statement: majority ? positive : negative,
    counter: majority ? negative : positive,
    agreement,
    invariant: agreement >= INVARIANT_THRESHOLD,
  };
}

/**
 * The property set is fixed and is applied identically to every response.
 * It cannot be tuned per run — a per-run property list is a way of choosing
 * the questions after seeing the answers.
 */
export function measureProperties(
  per: GeneratorResult[],
  boltzmann: BoltzmannLeg,
): PropertyAgreement[] {
  if (!per.length) return [];
  // A band-scale reference so "small" is expressed in the ensemble's own
  // units rather than in percentage points pulled out of the air.
  // 3.29 sigma spans p5..p95 for a Gaussian.
  const bandSigma = Math.abs(boltzmann.quantiles.p95 - boltzmann.quantiles.p5) / 3.29;

  return [
    agreementOf(per,
      "the median forward return is negative",
      "the median forward return is positive",
      (g) => g.median < 0),
    agreementOf(per,
      "P(down) is above 50%",
      "P(down) is at or below 50%",
      (g) => g.p_down > 0.5),
    agreementOf(per,
      "P(down) clears 60%",
      "P(down) does not clear 60%",
      (g) => g.p_down > 0.6),
    agreementOf(per,
      "the 90% band straddles zero",
      "the 90% band excludes zero",
      (g) => g.quantiles.p5 < 0 && g.quantiles.p95 > 0),
    agreementOf(per,
      "the conditional shift is smaller than a quarter of the band sigma",
      "the conditional shift exceeds a quarter of the band sigma",
      (g) => bandSigma > 0 && Math.abs(g.median) < 0.25 * bandSigma),
    agreementOf(per,
      "dispersion is wider than the single-rule Boltzmann band",
      "dispersion is at or below the single-rule Boltzmann band",
      (g) => (g.quantiles.p95 - g.quantiles.p5) >
             (boltzmann.quantiles.p95 - boltzmann.quantiles.p5)),
  ];
}

/* ---------------- per-axis variance decomposition ---------------- */

export interface AxisShare {
  axis: AxisName;
  /** eta-squared: between-level sum of squares / total sum of squares */
  eta2: number;
  levels: { level: string; key: string; mean: number; n: number }[];
}

export interface VarianceReadout {
  shares: AxisShare[];
  /** 1 - sum(eta2). Interactions between axes plus sampling noise. */
  residual: number;
  /** the metric these shares decompose */
  metric: "median" | "p_down";
  total: number;
}

/**
 * Which axis moves the answer? One-way eta-squared per axis on the 144
 * per-generator values: between-level SS over total SS. The grid is a
 * balanced full factorial, so the four shares are comparable and what is left
 * over is interaction plus sampling noise, reported rather than hidden.
 *
 * If the drift axis dominates, this is where it becomes visible — which is
 * the point of the readout, not a bug in it.
 */
export function axisVariance(
  per: GeneratorResult[],
  metric: "median" | "p_down" = "median",
): VarianceReadout {
  const vals = per.map((g) => (metric === "median" ? g.median : g.p_down));
  const usable = vals.filter((v) => Number.isFinite(v));
  const gm = meanOf(usable);
  const total = usable.reduce((a, v) => a + (v - gm) * (v - gm), 0);

  const shares: AxisShare[] = AXIS_ORDER.map((axis) => {
    const levels = (RULE_AXES[axis] as readonly string[]).map((level) => {
      const grp = per
        .filter((g) => g.rule[axis] === level)
        .map((g) => (metric === "median" ? g.median : g.p_down))
        .filter((v) => Number.isFinite(v));
      return { level, key: levelKey(axis, level), mean: meanOf(grp), n: grp.length };
    });
    const between = levels.reduce((a, l) => a + l.n * (l.mean - gm) * (l.mean - gm), 0);
    return { axis, eta2: total > 0 ? between / total : 0, levels };
  });

  const sum = shares.reduce((a, s) => a + s.eta2, 0);
  return {
    shares: [...shares].sort((a, b) => b.eta2 - a.eta2),
    residual: Math.max(0, 1 - sum),
    metric,
    total,
  };
}

/** How many of the frozen grid actually came back with usable numbers. */
export function gridCoverage(res: RulialResponse): {
  ran: number; failed: number; expected: number; complete: boolean;
} {
  const per = res.rulial?.per_generator ?? [];
  const ran = per.filter(
    (g) => !g.failed && Number.isFinite(g.median) && Number.isFinite(g.p_down),
  ).length;
  const reported = res.rulial?.n_failed;
  const failed = typeof reported === "number" ? reported : EXPECTED_GENERATORS - ran;
  return {
    ran,
    failed: Math.max(0, failed),
    expected: EXPECTED_GENERATORS,
    complete: ran === EXPECTED_GENERATORS,
  };
}
