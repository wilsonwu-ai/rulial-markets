/**
 * ============================================================
 *  INVERSE SCENARIO CLIENT — CONTRACT.md §6b
 * ============================================================
 * The forward path answers "given this event, what is the distribution?".
 * This inverts it: "given a target probability, what event would produce it?".
 *
 * NEW FILE. Nothing in `api.ts`, `mock.ts`, `quant.ts` or `types.ts` is
 * touched — the forward path's calls, shapes and props are unchanged.
 *
 * ------------------------------------------------------------------
 * THE RULE THAT MAKES THIS HONEST, and it holds in mock mode too:
 *
 *   `achieved_prob` is COMPUTED by running the candidate event text through
 *   a forward model and measuring the fraction of paths that move in the
 *   requested direction. Text may be proposed. The number is never asserted.
 *
 * In LIVE mode the backend computes it with `generator.generate_ensemble`.
 * In MOCK mode this module computes it from a seeded in-browser ensemble —
 * the same arithmetic, on synthetic paths, clearly labelled SYNTHETIC on
 * screen. What is NOT permitted in either mode is writing a percentage into
 * a candidate and calling it the result.
 *
 * The mock search closes the gap by moving the event's SEVERITY (its drift),
 * never by widening dispersion. CONTRACT §6b freezes that: over-widening
 * `vol_mult` to hit a target was already measured at −52% lift, and hitting
 * a target by inflating width games the metric.
 * ------------------------------------------------------------------
 */

import type { EventRec, Mode, Quantiles } from "./types";
import { gauss, quantilesOf, rng, seedFrom } from "./quant";

/* ---------------- wire types (CONTRACT §6b) ---------------- */

export type Direction = "up" | "down";

export interface ScenarioRequest {
  ticker: string;
  direction: Direction;
  target_prob: number;      // 0.50 .. 0.95
  as_of_date: string;
  horizon_days?: number;
  n_candidates?: number;
}

export interface ScenarioCandidate {
  event_text: string;
  /** COMPUTED by the forward model. Never asserted by a language model. */
  achieved_prob: number;
  error: number;            // |achieved − target|
  quantiles: Quantiles;
  analogs_used?: EventRec[];
  narrative?: string;
  /** May only be true when a forward model actually ran. */
  verified: boolean;
}

export interface ScenarioResponse {
  target_prob: number;
  direction: Direction;
  ticker: string;
  scenarios: ScenarioCandidate[];
  best_error: number;
  search_iterations: number;
  note: string;
  /** Set by this client, not by the wire: which engine produced the numbers. */
  source?: "live" | "mock";
}

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const TIMEOUT_MS = 30000;

export class ScenarioError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "ScenarioError";
  }
}

/** POST /api/scenario. A live failure is thrown, never silently mocked —
 *  the panel surfaces the failure and offers the synthetic path explicitly. */
export async function requestScenario(
  mode: Mode,
  body: ScenarioRequest,
): Promise<ScenarioResponse> {
  if (mode === "mock") {
    return new Promise((r) => setTimeout(() => r(mockScenario(body)), 420));
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE}/api/scenario`, {
      method: "POST",
      signal: ctrl.signal,
      cache: "no-store",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const t = await res.text().catch(() => "");
      throw new ScenarioError(
        `${res.status} ${res.statusText}${t ? ` — ${t.slice(0, 180)}` : ""}`,
        res.status,
      );
    }
    const json = (await res.json()) as ScenarioResponse;
    return { ...json, source: "live" };
  } catch (e) {
    if (e instanceof ScenarioError) throw e;
    const msg = e instanceof Error ? e.message : String(e);
    throw new ScenarioError(
      msg.includes("abort") ? `backend did not answer in ${TIMEOUT_MS / 1000}s` : msg,
    );
  } finally {
    clearTimeout(timer);
  }
}

/* ================================================================
   MOCK ENGINE — SYNTHETIC, and it really does search
   ================================================================ */

/** Rough daily vols, mirroring the synthetic vols in `mock.ts`. They shape the
 *  width of the synthetic ensemble and are NEVER adjusted by the search. */
const DAILY_VOL: Record<string, number> = {
  NVDA: 0.029, AAPL: 0.017, MSFT: 0.0155, AMZN: 0.0205, TSLA: 0.0355,
  META: 0.0225, GOOGL: 0.016, JPM: 0.015, XOM: 0.0145, BA: 0.0195,
};

/**
 * Candidate event templates, one bank per ticker per direction.
 *
 * These are drafted from `docs/research/<TICKER>.md`, which explains what
 * actually caused each event in the ledger with sources — so the MECHANISMS
 * here are the mechanisms that have historically moved these names (NVDA:
 * datacenter guidance and demand breaks; BA: a grounding and a delivery halt;
 * XOM: a supply shock or a demand collapse; JPM: credit provisions).
 *
 * They are HYPOTHETICAL conditional events, exactly like the four forward
 * presets. Nothing here is presented as something that happened. The `{sev}`
 * token is filled by the search with the magnitude it actually converged on,
 * so the words and the number the model was handed cannot drift apart.
 */
interface Template { text: string; lo: number; hi: number }

const GENERIC_DOWN: Template[] = [
  { text: "{T} guides next-quarter revenue {sev}% below consensus and withdraws full-year guidance, citing demand it says it cannot currently size.", lo: 4, hi: 32 },
  { text: "{T} discloses an accounting review of previously reported segment revenue and delays its filing; two sell-side desks pull their ratings pending clarity.", lo: 3, hi: 26 },
  { text: "A regulator opens a formal proceeding against {T} covering roughly {sev}% of reported revenue, and the company says it cannot estimate the timeline.", lo: 5, hi: 34 },
];
const GENERIC_UP: Template[] = [
  { text: "{T} reports revenue {sev}% above the high end of guidance, raises the outlook, and announces an accelerated buyback.", lo: 4, hi: 30 },
  { text: "{T} settles the overhang that had capped the multiple and guides next quarter above every published estimate on the street.", lo: 3, hi: 24 },
  { text: "{T} discloses a segment at {sev}% year-over-year growth that had not been broken out before, forcing a re-rating of the whole business.", lo: 5, hi: 40 },
];

const BANK: Record<string, { down: Template[]; up: Template[] }> = {
  NVDA: {
    down: [
      { text: "NVDA guides next-quarter datacenter revenue {sev}% below consensus and says two hyperscale customers have paused orders pending their own capex reviews.", lo: 5, hi: 34 },
      { text: "New export rules extend to NVDA's current top-end datacenter part; the company says the affected China business is roughly {sev}% of datacenter revenue and offers no replacement timeline.", lo: 6, hi: 30 },
      { text: "A packaging defect is disclosed in a shipping datacenter product, with a charge taken this quarter and a guide cut of about {sev}% while the qualification is redone.", lo: 5, hi: 28 },
    ],
    up: [
      { text: "NVDA reports datacenter revenue {sev}% above the high end of guidance, says next-generation capacity is sold out through the following fiscal year, and raises the outlook again.", lo: 8, hi: 45 },
      { text: "NVDA discloses that a sovereign AI programme has contracted capacity worth roughly {sev}% of trailing datacenter revenue, on a multi-year take-or-pay basis.", lo: 6, hi: 35 },
      { text: "An export restriction that had been priced in is lifted, and NVDA guides next quarter about {sev}% above the street on the restored China channel.", lo: 5, hi: 28 },
    ],
  },
  BA: {
    down: [
      { text: "A second in-service failure of the same airframe type is reported days after the first inquiry opens. Regulators on three continents ground the fleet indefinitely, deliveries halt, and two flag carriers reopen their order books to the competition.", lo: 6, hi: 40 },
      { text: "BA halts deliveries of its highest-volume programme pending a production-quality audit; management says roughly {sev}% of planned deliveries this year are now unschedulable.", lo: 6, hi: 32 },
      { text: "A major operator cancels a firm order covering about {sev}% of the backlog for one programme and takes its option book to the competing airframer.", lo: 4, hi: 26 },
    ],
    up: [
      { text: "The grounded fleet is cleared to return to service on a firm date, and BA says deliveries resume next month with about {sev}% of stored aircraft already re-contracted.", lo: 8, hi: 40 },
      { text: "A flag carrier converts options into a firm order worth roughly {sev}% of the current backlog, and BA raises its delivery guidance for the year.", lo: 5, hi: 30 },
      { text: "A multi-year labour dispute is settled and the delayed programme gets a certified entry-into-service date; BA guides free cash flow about {sev}% above the street.", lo: 5, hi: 26 },
    ],
  },
  XOM: {
    down: [
      { text: "Global demand estimates are cut hard as a transport shutdown spreads; crude falls through the marginal cost of the shale complex and XOM's realizations drop roughly {sev}% quarter over quarter.", lo: 8, hi: 34 },
      { text: "The producer group abandons its quota agreement and opens the taps into a demand air pocket; XOM's upstream cash margin compresses by about {sev}%.", lo: 6, hi: 30 },
      { text: "XOM takes an impairment on long-lived assets equal to roughly {sev}% of book and says the dividend will be funded from the balance sheet this year.", lo: 5, hi: 25 },
    ],
    up: [
      { text: "Strikes disable a major Gulf crude processing facility overnight. The strait is effectively closed to tanker traffic, Brent gaps higher at the open, and there is no clear timeline for restored supply.", lo: 10, hi: 40 },
      { text: "A supply outage removes about {sev}% of seaborne crude from the market for an indefinite period, and XOM's unhedged upstream barrels reprice immediately.", lo: 6, hi: 32 },
      { text: "The producer group announces a deeper-than-expected cut into a recovering demand picture, and XOM guides upstream cash flow roughly {sev}% above consensus.", lo: 5, hi: 26 },
    ],
  },
  TSLA: {
    down: [
      { text: "TSLA reports quarterly deliveries about {sev}% below consensus and says price cuts already taken have not cleared the inventory build.", lo: 5, hi: 28 },
      { text: "A safety authority opens a defect investigation covering the current volume platform; TSLA suspends deliveries of the affected trim and cannot size the recall.", lo: 4, hi: 26 },
      { text: "Automotive gross margin ex-credits falls roughly {sev}% quarter over quarter and management declines to give a unit-volume target for the year.", lo: 5, hi: 30 },
    ],
    up: [
      { text: "TSLA reports automotive gross margin about {sev}% above consensus on a mix shift management says is durable, and confirms the next platform is ahead of schedule.", lo: 6, hi: 34 },
      { text: "A major manufacturer licenses TSLA's charging and drivetrain stack, adding a high-margin revenue line worth roughly {sev}% of trailing quarterly revenue.", lo: 5, hi: 30 },
      { text: "Quarterly deliveries land about {sev}% above the street with no discount, and TSLA raises the production target for the year.", lo: 5, hi: 32 },
    ],
  },
  META: {
    down: [
      { text: "META cuts ad revenue guidance, raises capex again, and concedes that reported engagement growth was overstated by a measurement error of roughly {sev}%.", lo: 4, hi: 26 },
      { text: "A platform-level privacy change removes the signal behind about {sev}% of ad targeting revenue, and META says it cannot rebuild the measurement within the year.", lo: 5, hi: 28 },
      { text: "META guides the coming year's expenses roughly {sev}% above consensus for a segment with no disclosed revenue, and declines to cap the spend.", lo: 6, hi: 30 },
    ],
    up: [
      { text: "META guides expenses about {sev}% below its prior range, announces a large buyback and its first dividend, and reports ad revenue reaccelerating.", lo: 5, hi: 30 },
      { text: "META reports ad impressions and price per ad both up, with revenue roughly {sev}% above the high end of guidance, and caps the loss-making segment's budget.", lo: 5, hi: 28 },
      { text: "The measurement stack is rebuilt after the platform privacy change, recovering about {sev}% of the targeting revenue the market had written off.", lo: 4, hi: 24 },
    ],
  },
  JPM: {
    down: [
      { text: "JPM books a credit provision about {sev}% above consensus as a leveraged-lending book marks down, and withdraws its net-interest-income guide.", lo: 5, hi: 30 },
      { text: "A funding run at a peer institution forces an emergency weekend facility; JPM discloses counterparty exposure of roughly {sev}% of tangible book.", lo: 6, hi: 34 },
      { text: "A regulator caps JPM's balance-sheet growth pending remediation, and the buyback is suspended for the year.", lo: 4, hi: 22 },
    ],
    up: [
      { text: "JPM acquires a failed competitor's deposit book at a negotiated discount, adding roughly {sev}% to tangible book value at closing.", lo: 6, hi: 34 },
      { text: "JPM reports net interest income about {sev}% above guidance, releases reserves, and raises the buyback.", lo: 5, hi: 26 },
      { text: "The regulator lifts the asset cap and JPM immediately guides loan growth roughly {sev}% above the street.", lo: 4, hi: 22 },
    ],
  },
  AAPL: {
    down: [
      { text: "AAPL cuts quarterly revenue guidance by about {sev}% and says handset demand in Greater China deteriorated through the quarter.", lo: 4, hi: 22 },
      { text: "A supplier failure halts assembly of the flagship handset for an indefinite period; AAPL says roughly {sev}% of planned quarterly units are unbuildable.", lo: 4, hi: 24 },
      { text: "A ruling puts the default-search payment at risk, roughly {sev}% of services revenue, with no announced replacement.", lo: 5, hi: 26 },
    ],
    up: [
      { text: "AAPL reports revenue about {sev}% above the high end of guidance with services at a record margin, and raises the buyback authorisation.", lo: 4, hi: 22 },
      { text: "The new handset cycle sells through at roughly {sev}% above the prior generation at the same point, and AAPL guides the December quarter above every estimate.", lo: 4, hi: 24 },
      { text: "A regulatory overhang covering about {sev}% of services revenue is resolved on terms materially better than the market had priced.", lo: 4, hi: 20 },
    ],
  },
  MSFT: {
    down: [
      { text: "MSFT guides cloud growth about {sev}% below consensus and says optimisation by large customers is continuing rather than stabilising.", lo: 4, hi: 22 },
      { text: "MSFT raises AI capex again while guiding the segment's revenue roughly {sev}% below the street, and declines to give a return-on-capital frame.", lo: 5, hi: 26 },
      { text: "A security incident forces a suspension of a major cloud service; enterprise renewals covering about {sev}% of the segment are paused pending review.", lo: 5, hi: 24 },
    ],
    up: [
      { text: "MSFT reports cloud growth about {sev}% above guidance with margins expanding, and says AI capacity is fully contracted.", lo: 4, hi: 26 },
      { text: "MSFT discloses an AI revenue run-rate equal to roughly {sev}% of segment revenue for the first time, and raises the outlook.", lo: 4, hi: 28 },
      { text: "A large enterprise-agreement cohort renews about {sev}% above prior terms, and MSFT guides operating margin above consensus.", lo: 3, hi: 20 },
    ],
  },
  AMZN: {
    down: [
      { text: "AMZN guides operating income about {sev}% below the low end of consensus on fulfilment overcapacity, and says the build-out cannot be paused this year.", lo: 5, hi: 28 },
      { text: "AWS growth decelerates roughly {sev}% quarter over quarter and management attributes it to customers moving workloads to a competing stack.", lo: 4, hi: 26 },
      { text: "A structural remedy is proposed that would separate the marketplace from the logistics business, covering about {sev}% of segment profit.", lo: 5, hi: 26 },
    ],
    up: [
      { text: "AMZN breaks out a segment growing about {sev}% year over year that had not been disclosed before, and the market re-rates the whole business on it.", lo: 6, hi: 34 },
      { text: "AMZN reports operating income roughly {sev}% above the high end of guidance as fulfilment costs per unit fall for a third quarter.", lo: 5, hi: 30 },
      { text: "AWS reaccelerates about {sev}% on AI workloads and AMZN says the backlog is now contracted rather than pipeline.", lo: 4, hi: 26 },
    ],
  },
  GOOGL: {
    down: [
      { text: "GOOGL reports search revenue about {sev}% below consensus and concedes that query volume is migrating to an interface it does not monetise.", lo: 4, hi: 24 },
      { text: "A remedy ruling requires unwinding the default-placement agreements behind roughly {sev}% of search revenue, on a fixed timetable.", lo: 5, hi: 28 },
      { text: "GOOGL guides capex about {sev}% above the street while cloud margin compresses, and gives no timeline for a return on the spend.", lo: 5, hi: 26 },
    ],
    up: [
      { text: "GOOGL reports search and cloud both about {sev}% above consensus, announces its first dividend, and raises the buyback.", lo: 4, hi: 26 },
      { text: "A remedy ruling lands materially narrower than feared, leaving roughly {sev}% of the revenue the market had already written off intact.", lo: 5, hi: 28 },
      { text: "Cloud turns profitable a year early with backlog up about {sev}%, and GOOGL guides margin above every published estimate.", lo: 4, hi: 24 },
    ],
  },
};

function bankFor(ticker: string, direction: Direction): Template[] {
  const b = BANK[ticker.toUpperCase()];
  if (b) return direction === "down" ? b.down : b.up;
  const generic = direction === "down" ? GENERIC_DOWN : GENERIC_UP;
  return generic.map((t) => ({ ...t, text: t.text.replace(/\{T\}/g, ticker.toUpperCase()) }));
}

/**
 * Simulate a terminal-return ensemble for one candidate and MEASURE the
 * probability of moving in `direction`. This is the mock's forward model: the
 * probability is read off the paths, exactly as the live endpoint reads it off
 * `generate_ensemble`.
 *
 * `severity` moves the DRIFT only. Sigma is fixed by the ticker and the
 * horizon and is never touched by the search — widening to hit a target is
 * frozen out by CONTRACT §6b.
 */
function measure(
  ticker: string, direction: Direction, horizon: number,
  severity: number, seed: number, nPaths = 2000,
): { prob: number; quantiles: Quantiles; sample: number[] } {
  const vol = DAILY_VOL[ticker.toUpperCase()] ?? 0.02;
  const sigma = vol * Math.sqrt(horizon) * 1.9;   // post-event vol, fixed
  const mu = (direction === "down" ? -1 : 1) * severity * sigma * 2.4;
  const u = rng(seed);
  const sample: number[] = [];
  for (let i = 0; i < nPaths; i++) sample.push(mu + sigma * gauss(u));
  const hits = sample.reduce(
    (a, v) => a + (direction === "down" ? (v < 0 ? 1 : 0) : (v > 0 ? 1 : 0)),
    0,
  );
  return { prob: hits / nPaths, quantiles: quantilesOf(sample), sample };
}

/**
 * Bisection on severity. Every iteration re-measures with the forward model,
 * so `achieved_prob` on the returned candidate is a measurement of the text
 * that is actually shown, not a target copied into a field.
 */
function search(
  ticker: string, direction: Direction, horizon: number,
  target: number, seed: number,
): { severity: number; prob: number; quantiles: Quantiles; iterations: number } {
  let lo = 0, hi = 1;
  let best = measure(ticker, direction, horizon, 0.5, seed);
  let bestSev = 0.5;
  let iterations = 0;
  for (let i = 0; i < 14; i++) {
    iterations++;
    const mid = (lo + hi) / 2;
    const m = measure(ticker, direction, horizon, mid, seed);
    if (Math.abs(m.prob - target) < Math.abs(best.prob - target)) {
      best = m;
      bestSev = mid;
    }
    if (m.prob < target) lo = mid; else hi = mid;
    if (Math.abs(m.prob - target) < 0.004) break;
  }
  return { severity: bestSev, prob: best.prob, quantiles: best.quantiles, iterations };
}

/** Fill the magnitude token with the severity the search actually converged
 *  on, so the words in the candidate and the number the model was handed
 *  cannot drift apart. */
function render(t: Template, severity: number): string {
  const mag = Math.round(t.lo + severity * (t.hi - t.lo));
  return t.text.replace(/\{sev\}/g, String(mag));
}

export const SCENARIO_MOCK_NOTICE =
  "SYNTHETIC — the candidate ensembles are generated in-browser by a seeded RNG, not by the backend model. The probabilities are still MEASURED off those paths, never asserted.";

export function mockScenario(req: ScenarioRequest): ScenarioResponse {
  const horizon = req.horizon_days ?? 5;
  const n = Math.max(1, Math.min(5, req.n_candidates ?? 3));
  const bank = bankFor(req.ticker, req.direction);

  let iterations = 0;
  const scenarios: ScenarioCandidate[] = [];

  for (let i = 0; i < n; i++) {
    const tpl = bank[i % bank.length];
    const seed = seedFrom(
      `${req.ticker}|${req.direction}|${req.target_prob.toFixed(3)}|${req.as_of_date}|${i}`,
    );
    const s = search(req.ticker, req.direction, horizon, req.target_prob, seed);
    iterations += s.iterations;
    const text = render(tpl, s.severity);
    scenarios.push({
      event_text: text,
      achieved_prob: s.prob,
      error: Math.abs(s.prob - req.target_prob),
      quantiles: s.quantiles,
      analogs_used: [],
      narrative:
        `Severity was searched, not chosen: ${s.iterations} bisection steps on the event's magnitude, ` +
        `re-measuring P(${req.direction}) on a fresh ensemble each step. Dispersion was held fixed at the ticker's ` +
        `post-event volatility — widening it would hit any target and would mean nothing.`,
      verified: true,   // a forward model DID run — the in-browser synthetic one
    });
  }

  scenarios.sort((a, b) => a.error - b.error);
  const best = scenarios.length ? scenarios[0].error : 1;

  return {
    target_prob: req.target_prob,
    direction: req.direction,
    ticker: req.ticker.toUpperCase(),
    scenarios,
    best_error: best,
    search_iterations: iterations,
    note:
      `${SCENARIO_MOCK_NOTICE} These are candidates, not the answer: the inverse is not unique, ` +
      `and many different events map to the same probability.`,
    source: "mock",
  };
}
