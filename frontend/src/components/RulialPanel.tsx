"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Mode } from "@/lib/types";
import { pct, pctPlain } from "@/lib/quant";
import {
  AXIS_LABEL, AXIS_ORDER, EXPECTED_GENERATORS, INVARIANT_THRESHOLD, RULE_AXES,
  axisVariance, gridCoverage, levelKey, measureProperties, mockRulial,
  requestRulial, rulialNoise,
  type PropertyAgreement, type RulialNoise, type RulialResponse,
} from "@/lib/rulial";
import { RulialFan } from "./RulialFan";

/**
 * THE RULIAL SURFACE — CONTRACT.md §6d.
 *
 * Boltzmann varies the configuration under one rule. Rulial varies the rule.
 * Both are on screen at once, on purpose: the comparison is the argument, and
 * an ensemble that quietly dropped its own baseline would be making a claim it
 * had removed the means to check.
 *
 * Three things in here are load-bearing and none of them may be softened:
 *
 *  1. The grid is 144 and the coverage line says how many of the 144 actually
 *     returned. A short grid is stated in words, never absorbed into a
 *     percentage that still reads as complete.
 *  2. Every agreement fraction, the `reducible` verdict and the per-axis
 *     variance shares are MEASURED from the returned per-generator
 *     distributions by `lib/rulial.ts`. This component formats numbers; it
 *     cannot produce one.
 *  3. INVARIANT and RULE-DEPENDENT are two visually distinct lists, and the
 *     rule-dependent list carries its prohibition in the header rather than in
 *     a footnote. A property that flips across the grid is not skill, and the
 *     one place that mistake gets made is a UI that renders both lists the
 *     same way.
 */
export function RulialPanel({
  ticker, asOf, text, horizon, mode,
}: {
  ticker: string;
  asOf: string;
  text: string;
  horizon: number;
  mode: Mode;
}) {
  const [running, setRunning] = useState(false);
  const [res, setRes] = useState<RulialResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [metric, setMetric] = useState<"median" | "p_down">("median");
  /* Measured Monte Carlo noise on sign agreement, shipped beside the
     precomputed runs. Loaded regardless of mode because it is a property of
     the estimator, not of this particular run — and because a bare
     "71.5%" on a quantity that moves 6.9 points on a re-seed is a
     precise-looking number that is not precise. */
  const [noise, setNoise] = useState<RulialNoise | null>(null);
  useEffect(() => {
    let dead = false;
    void rulialNoise().then((n) => { if (!dead) setNoise(n); });
    return () => { dead = true; };
  }, []);

  /* 1,000 to match the path budget at which the Monte Carlo noise floor on
     sign agreement was actually MEASURED (rulial_index.json `_noise`). Running
     the live grid at a different budget than the measurement would put a band
     on screen that was calibrated for someone else's run. The backend does 144
     generators at this budget in ~2s. */
  const nPerRule = 1000;
  const highlight = hover ?? pinned;

  const run = useCallback(async () => {
    setRunning(true);
    setErr(null);
    try {
      const r = await requestRulial(mode, {
        ticker, event_text: text, as_of_date: asOf,
        horizon_days: horizon, n_paths_per_rule: nPerRule,
      });
      setRes(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [mode, ticker, text, asOf, horizon]);

  // Memoised because `?? []` would otherwise mint a new array every render
  // and re-run the measurement below on every keystroke elsewhere in the page.
  const per = useMemo(() => res?.rulial?.per_generator ?? [], [res]);
  const cov = res ? gridCoverage(res) : null;

  /* Measured in-browser from whatever the engine returned, live or synthetic.
     Same estimator either way, so the two sources are comparable. */
  const props = useMemo(
    () => (res ? measureProperties(per, res.boltzmann) : []),
    [res, per],
  );
  const variance = useMemo(
    () => (per.length ? axisVariance(per, metric) : null),
    [per, metric],
  );

  const invariants = props.filter((p) => p.invariant);
  const dependent = props.filter((p) => !p.invariant);

  return (
    <div className="grid gap-8">
      {/* ---------------- run control ---------------- */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-4">
        <button
          onClick={() => void run()}
          disabled={running}
          className="btn-primary"
        >
          {running ? `Sampling ${EXPECTED_GENERATORS} generators…` : `Sample the ${EXPECTED_GENERATORS} generators`}
        </button>
        <span className="text-sm leading-relaxed text-[var(--color-ink-faint)]">
          <span className="num">{ticker}</span> · as-of <span className="num">{asOf}</span> ·{" "}
          <span className="num">{horizon}d</span> forward ·{" "}
          <span className="num">{nPerRule}</span> paths per rule ·{" "}
          <span className="num">{(EXPECTED_GENERATORS * nPerRule).toLocaleString()}</span> paths total
        </span>
        {res && <SourceBadge source={res.source ?? mode} />}
      </div>

      {err && (
        <div className="rounded-lg border border-[var(--color-neg)] bg-[#FDF3F2] px-6 py-5">
          <div className="label" style={{ color: "var(--color-neg)" }}>rulial engine error</div>
          <div className="num mt-2 text-sm text-[var(--color-ink-dim)]">{err}</div>
          <button
            onClick={() => { setErr(null); setRes(mockRulial({
              ticker, event_text: text, as_of_date: asOf,
              horizon_days: horizon, n_paths_per_rule: nPerRule,
            })); }}
            className="btn-secondary mt-4 bg-white"
          >
            Run the synthetic grid instead
          </button>
        </div>
      )}

      {!res && !err && (
        <div className="flex min-h-[280px] flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-[var(--color-gray-400)] px-6 py-12 text-center">
          <div className="label-title" style={{ fontSize: "1.5rem", color: "var(--color-ink-faint)" }}>
            one rule, or one hundred and forty-four
          </div>
          <p className="max-w-[62ch] text-base leading-relaxed text-[var(--color-ink-faint)]">
            A Boltzmann ensemble asks how uncertain the outcome is <em>given the model is right</em>.
            The rulial ensemble asks how uncertain we are <em>given we do not know which rule
            generates reality</em>. Sampling draws both, and the width of the gap between them is
            the honest error bar.
          </p>
        </div>
      )}

      {res && (
        <>
          {/* ---------------- headline measurements ---------------- */}
          <div className="grid gap-px overflow-hidden rounded-lg border border-[var(--color-rule)] bg-[var(--color-rule)] sm:grid-cols-2 xl:grid-cols-4">
            <SignAgreement
              agreement={res.rulial.consensus.sign_agreement}
              ran={cov?.ran ?? per.length}
              noise={noise}
              ranPaths={res.diagnostics?.n_paths_per_rule ?? nPerRule}
            />
            <Tile
              label="do the rules agree?"
              value={res.rulial.consensus.reducible ? "YES — A REDUCIBLE POCKET" : "NO — RULE-DEPENDENT"}
              sub={`measured against the frozen ${pctPlain(INVARIANT_THRESHOLD, 0)} agreement threshold — not asserted`}
              tone={res.rulial.consensus.reducible ? "pos" : undefined}
              big
            />
            <Tile
              label="median band"
              value={`${pct(res.rulial.consensus.median_band[0])} … ${pct(res.rulial.consensus.median_band[1])}`}
              sub={`Boltzmann alone says ${pct(res.boltzmann.median)}`}
            />
            <Tile
              label="P(down) band"
              value={`${pctPlain(res.rulial.consensus.p_down_band[0], 1)} … ${pctPlain(res.rulial.consensus.p_down_band[1], 1)}`}
              sub={`Boltzmann alone says ${pctPlain(res.boltzmann.p_down, 1)}`}
            />
          </div>

          {/* ---------------- grid coverage. Never rounded away. ---------------- */}
          {cov && (
            <div
              className={cov.complete ? "callout px-6 py-4" : "callout-notice px-6 py-4"}
            >
              <span
                className="label-title"
                style={{ color: cov.complete ? "var(--color-blue)" : "var(--color-notice)" }}
              >
                {cov.ran} of {cov.expected} rules ran · {cov.failed} failed
              </span>
              <span className="ml-4 text-sm text-[var(--color-ink-dim)]">
                {cov.complete
                  ? "The full frozen grid returned. No axis was pruned; the grid is 144 and fixed by CONTRACT §6d."
                  : `${cov.failed} generator${cov.failed === 1 ? "" : "s"} did not return. Every fraction below is over the ${cov.ran} that did, and is stated as such rather than presented as full coverage.`}
              </span>
            </div>
          )}

          {/* ---------------- the picture ---------------- */}
          <RulialFan
            per={per}
            boltzmann={res.boltzmann}
            horizon={horizon}
            highlight={highlight}
          />

          {/* ---------------- axis highlight chips ---------------- */}
          <div>
            <div className="mb-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <span className="label">isolate an axis</span>
              <span className="text-sm text-[var(--color-ink-faint)]">
                hover or click a level to light up only the rules that use it. If one axis splits
                the fan into separate sheaves, that axis is the one carrying the answer.
              </span>
              {pinned && (
                <button className="btn-secondary ml-auto" onClick={() => setPinned(null)}>
                  Clear
                </button>
              )}
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {AXIS_ORDER.map((axis) => (
                <div key={axis} className="rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] p-4">
                  <div className="label mb-3">{AXIS_LABEL[axis]}</div>
                  <div className="flex flex-wrap gap-2">
                    {(RULE_AXES[axis] as readonly string[]).map((level) => {
                      const k = levelKey(axis, level);
                      const on = pinned === k;
                      return (
                        <button
                          key={level}
                          aria-pressed={on}
                          onMouseEnter={() => setHover(k)}
                          onMouseLeave={() => setHover(null)}
                          onFocus={() => setHover(k)}
                          onBlur={() => setHover(null)}
                          onClick={() => setPinned(on ? null : k)}
                          className="num rounded-full border px-3 py-1 text-xs font-semibold transition-colors"
                          style={{
                            borderColor: on ? "var(--color-blue)" : "var(--color-gray-400)",
                            background: on ? "var(--color-blue)" : "var(--color-gray-000)",
                            color: on ? "#fff" : "var(--color-ink-dim)",
                          }}
                        >
                          {level}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ---------------- variance + the two lists ---------------- */}
          <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            {variance && <AxisVariance v={variance} metric={metric} setMetric={setMetric} />}
            <Findings invariants={invariants} dependent={dependent} engine={res} />
          </div>

          {res.note && (
            <p className="max-w-[100ch] border-l-[3px] border-[var(--color-blue)] pl-5 text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
              {res.note}
            </p>
          )}
        </>
      )}
    </div>
  );
}

/* ================================================================ */

function SourceBadge({ source }: { source: Mode }) {
  const map: Record<Mode, { text: string; color: string; bg: string }> = {
    live: { text: "LIVE ENGINE", color: "var(--color-blue)", bg: "var(--color-blue-tint)" },
    baked: { text: "PRECOMPUTED · REAL", color: "var(--color-blue)", bg: "var(--color-blue-tint)" },
    mock: { text: "SYNTHETIC · NOT MODEL OUTPUT", color: "var(--color-notice)", bg: "var(--color-notice-tint)" },
  };
  const s = map[source];
  return (
    <span
      className="label-title ml-auto rounded-full px-4 py-1.5"
      style={{ color: s.color, background: s.bg, border: `1px solid ${s.color}` }}
    >
      {s.text}
    </span>
  );
}

/**
 * SIGN AGREEMENT, AS A BAND.
 *
 * Re-seeding the SAME frozen grid at 1,000 paths per rule moved this fraction
 * by 6.9 percentage points across four seeds — that measurement ships in
 * `rulial_index.json` beside the runs. Printing "71.5%" implies a resolution
 * the estimator does not have, so the headline is the band and the centre is
 * the sub-line. Where no noise measurement is available the panel says that
 * instead of quietly reverting to a precise-looking figure.
 */
function SignAgreement({
  agreement, ran, noise, ranPaths,
}: { agreement: number; ran: number; noise: RulialNoise | null; ranPaths?: number }) {
  const half = noise ? noise.spread / 2 : null;
  const lo = half != null ? Math.max(0, agreement - half) : null;
  const hi = half != null ? Math.min(1, agreement + half) : null;
  const share = Math.round(agreement * ran);

  return (
    <div className="bg-[var(--color-panel)] px-6 py-5">
      <div className="label">how many rules agree on direction</div>
      <div className="figure mt-3 break-words" style={{ fontSize: "var(--fs-metric)", color: "var(--color-navy)" }}>
        {lo != null && hi != null
          ? `${pctPlain(lo, 0)}–${pctPlain(hi, 0)}`
          : pctPlain(agreement, 1)}
      </div>

      {/* the band on a 0-100 rule, with the frozen invariant threshold marked */}
      <svg viewBox="0 0 300 26" className="mt-3 w-full" role="img"
        aria-label={`Sign agreement band, centre ${(agreement * 100).toFixed(1)} percent`}>
        <line x1="2" x2="298" y1="13" y2="13" stroke="var(--color-gray-200)" strokeWidth="6" strokeLinecap="round" />
        {lo != null && hi != null && (
          <line
            x1={2 + lo * 296} x2={2 + hi * 296} y1="13" y2="13"
            stroke="var(--color-blue)" strokeWidth="8" strokeLinecap="round" opacity="0.45"
          />
        )}
        <line x1={2 + agreement * 296} x2={2 + agreement * 296} y1="3" y2="23"
          stroke="var(--color-navy)" strokeWidth="3" />
        <line x1={2 + INVARIANT_THRESHOLD * 296} x2={2 + INVARIANT_THRESHOLD * 296} y1="4" y2="22"
          stroke="var(--color-axis)" strokeWidth="2" strokeDasharray="3 3" />
      </svg>

      <div className="mt-2 text-sm leading-snug text-[var(--color-ink-faint)]">
        {noise ? (
          <>
            centre {pctPlain(agreement, 1)} ({share} of {ran} rules). Re-seeding the same grid at{" "}
            <span className="num">{noise.n_paths_per_rule.toLocaleString()}</span> paths per rule moved
            this by <span className="num">{(noise.spread * 100).toFixed(1)}</span> points across{" "}
            {noise.sign_agreement_samples.length} seeds
            {ranPaths && ranPaths < noise.n_paths_per_rule
              ? ` — and this run used only ${ranPaths.toLocaleString()} per rule, so treat that spread as a floor`
              : ""}
            . Read the band, not the figure. Dashed mark is the{" "}
            {pctPlain(INVARIANT_THRESHOLD, 0)} invariant threshold.
          </>
        ) : (
          <>
            {share} of {ran} rules share the median&rsquo;s sign. Monte Carlo noise on this fraction
            has not been measured for this run, so treat it as approximate rather than exact.
          </>
        )}
      </div>
    </div>
  );
}

function Tile({
  label, value, sub, big = false, tone,
}: {
  label: string; value: string; sub: string; big?: boolean; tone?: "pos" | "neg";
}) {
  const color =
    tone === "pos" ? "var(--color-pos)" : tone === "neg" ? "var(--color-neg)" : "var(--color-navy)";
  return (
    <div className="bg-[var(--color-panel)] px-6 py-5">
      <div className="label">{label}</div>
      <div
        className="figure mt-3 break-words"
        style={{ color, fontSize: big ? "var(--fs-metric)" : "1.5rem" }}
      >
        {value}
      </div>
      <div className="mt-3 text-sm leading-snug text-[var(--color-ink-faint)]">{sub}</div>
    </div>
  );
}

/* ---------------- per-axis variance ---------------- */

function AxisVariance({
  v, metric, setMetric,
}: {
  v: NonNullable<ReturnType<typeof axisVariance>>;
  metric: "median" | "p_down";
  setMetric: (m: "median" | "p_down") => void;
}) {
  const leader = v.shares[0];
  return (
    <div>
      <div className="mb-1 flex flex-wrap items-center gap-x-4 gap-y-2">
        <h3 className="label-title">Which axis moves the answer</h3>
        <div className="ml-auto flex gap-2">
          {(["median", "p_down"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              aria-pressed={metric === m}
              className="num rounded-full border px-3 py-1 text-xs font-semibold"
              style={{
                borderColor: metric === m ? "var(--color-blue)" : "var(--color-gray-400)",
                background: metric === m ? "var(--color-blue)" : "var(--color-gray-000)",
                color: metric === m ? "#fff" : "var(--color-ink-dim)",
              }}
            >
              {m === "median" ? "rule median" : "P(down)"}
            </button>
          ))}
        </div>
      </div>
      <p className="mb-5 text-sm leading-relaxed text-[var(--color-ink-faint)]">
        Share of the spread in the {metric === "median" ? "144 rule medians" : "144 P(down) values"} explained by
        each axis — between-level sum of squares over total, on the balanced full factorial.
        Measured from the returned generators.
      </p>

      <div className="grid gap-4">
        {v.shares.map((s, i) => (
          <div key={s.axis}>
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-base font-semibold text-[var(--color-navy)]">
                {AXIS_LABEL[s.axis]}
              </span>
              <span className="num text-base font-semibold" style={{ color: i === 0 ? "var(--color-blue)" : "var(--color-ink-dim)" }}>
                {pctPlain(s.eta2, 1)}
              </span>
            </div>
            <div className="mt-1.5 h-3 w-full overflow-hidden rounded-full bg-[var(--color-gray-100)] ring-1 ring-inset ring-[var(--color-gray-200)]">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.max(0.6, Math.min(100, s.eta2 * 100))}%`,
                  background: i === 0 ? "var(--color-blue)" : "var(--color-blue-light)",
                  transition: "width 320ms cubic-bezier(0.16,1,0.3,1)",
                }}
              />
            </div>
            <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1">
              {s.levels.map((l) => (
                <span key={l.level} className="num text-xs text-[var(--color-ink-faint)]">
                  {l.level}{" "}
                  <span style={{ color: "var(--color-ink-dim)", fontWeight: 600 }}>
                    {metric === "median" ? pct(l.mean) : pctPlain(l.mean, 1)}
                  </span>
                </span>
              ))}
            </div>
          </div>
        ))}

        <div>
          <div className="flex items-baseline justify-between gap-4">
            <span className="text-base text-[var(--color-ink-faint)]">interaction + sampling noise</span>
            <span className="num text-base text-[var(--color-ink-faint)]">{pctPlain(v.residual, 1)}</span>
          </div>
          <div className="mt-1.5 h-3 w-full overflow-hidden rounded-full bg-[var(--color-gray-100)] ring-1 ring-inset ring-[var(--color-gray-200)]">
            <div className="h-full rounded-full bg-[var(--color-gray-400)]"
              style={{ width: `${Math.max(0.6, Math.min(100, v.residual * 100))}%` }} />
          </div>
        </div>
      </div>

      {leader && (
        <p className="mt-5 rounded-lg bg-[var(--color-blue-tint)] px-5 py-4 text-[0.9375rem] leading-relaxed text-[var(--color-ink-dim)]">
          <span className="font-semibold text-[var(--color-navy)]">
            The {AXIS_LABEL[leader.axis]} axis explains {pctPlain(leader.eta2, 1)} of it.
          </span>{" "}
          {leader.axis === "drift_prior"
            ? "That is the whole point of building this. A Boltzmann ensemble varies configurations under one drift prior and therefore cannot see this axis at all — it would report the spread of one sheaf as the uncertainty. Anything that moves when the drift prior moves is a property of the prior, not a property of the market."
            : "Any property that moves with this axis is a property of that modelling choice, not a finding about the market."}
        </p>
      )}
    </div>
  );
}

/* ---------------- the two lists ---------------- */

function Findings({
  invariants, dependent, engine,
}: {
  invariants: PropertyAgreement[];
  dependent: PropertyAgreement[];
  engine: RulialResponse;
}) {
  return (
    // content-start so each list sizes to its own content: a stretched empty
    // INVARIANT box next to a full RULE-DEPENDENT one reads as missing data.
    <div className="grid content-start gap-6">
      <div className="rounded-lg border-l-4 border-[var(--color-pos)] bg-[#F2F8F4] p-6"
        style={{ borderTop: "1px solid var(--color-rule)", borderRight: "1px solid var(--color-rule)", borderBottom: "1px solid var(--color-rule)" }}>
        <div className="flex flex-wrap items-baseline gap-x-3">
          <h3 className="label-title" style={{ color: "var(--color-pos)" }}>Invariant</h3>
          <span className="num text-xs text-[var(--color-ink-faint)]">
            holds under ≥ {pctPlain(INVARIANT_THRESHOLD, 0)} of the grid · safe to state
          </span>
        </div>
        <ul className="mt-4 grid gap-3">
          {invariants.length === 0 && (
            <li className="text-[0.9375rem] text-[var(--color-ink-faint)]">
              Nothing cleared the threshold. Under this event text, no property of the forecast
              survives the change of rule — which is itself the result, and it is not a finding
              about the market.
            </li>
          )}
          {invariants.map((p) => (
            <li key={p.statement} className="flex items-baseline gap-3">
              <span className="num shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
                style={{ background: "var(--color-pos)", color: "#fff" }}>
                {pctPlain(p.agreement, 0)}
              </span>
              <span className="text-[0.9375rem] leading-snug text-[var(--color-ink)]">{p.statement}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg border-l-4 border-[var(--color-neg)] bg-[#FDF3F2] p-6"
        style={{ borderTop: "1px solid var(--color-rule)", borderRight: "1px solid var(--color-rule)", borderBottom: "1px solid var(--color-rule)" }}>
        <div className="flex flex-wrap items-baseline gap-x-3">
          <h3 className="label-title" style={{ color: "var(--color-neg)" }}>Rule-dependent</h3>
          <span className="num text-xs text-[var(--color-ink-faint)]">
            flips across the grid · MUST NOT be presented as skill (§6d)
          </span>
        </div>
        <ul className="mt-4 grid gap-3">
          {dependent.length === 0 && (
            <li className="text-[0.9375rem] text-[var(--color-ink-faint)]">
              Every tested property survived the change of rule. A genuine pocket of reducibility
              for this event text, at this grid resolution.
            </li>
          )}
          {dependent.map((p) => (
            <li key={p.statement} className="grid gap-1">
              <div className="flex items-baseline gap-3">
                <span className="num shrink-0 rounded px-1.5 py-0.5 text-xs font-semibold"
                  style={{ background: "var(--color-neg)", color: "#fff" }}>
                  {pctPlain(p.agreement, 0)}
                </span>
                <span className="text-[0.9375rem] leading-snug text-[var(--color-ink)]">{p.statement}</span>
              </div>
              <div className="num pl-[3.1rem] text-xs text-[var(--color-ink-faint)]">
                the other {pctPlain(1 - p.agreement, 0)} of rules say: {p.counter}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* The engine's own wording, shown only when a real engine produced it.
          In synthetic mode the strings are generated from the very same
          measurement rendered above, and printing them twice would dress one
          measurement up as two independent agreements. */}
      {engine.source !== "mock" && (engine.invariants?.length || engine.rule_dependent?.length) ? (
        <div className="rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] p-6">
          <div className="label mb-3">as reported by the engine</div>
          <ul className="grid gap-2">
            {(engine.invariants ?? []).map((s) => (
              <li key={`i-${s}`} className="text-sm leading-snug text-[var(--color-ink-dim)]">
                <span className="num mr-2 font-semibold" style={{ color: "var(--color-pos)" }}>INV</span>{s}
              </li>
            ))}
            {(engine.rule_dependent ?? []).map((s) => (
              <li key={`d-${s}`} className="text-sm leading-snug text-[var(--color-ink-dim)]">
                <span className="num mr-2 font-semibold" style={{ color: "var(--color-neg)" }}>DEP</span>{s}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
