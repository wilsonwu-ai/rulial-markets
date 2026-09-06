"use client";

import { useCallback, useMemo, useState } from "react";
import type { Mode } from "@/lib/types";
import { pct, pctPlain } from "@/lib/quant";
import {
  mockScenario, requestScenario,
  type Direction, type ScenarioCandidate, type ScenarioResponse,
} from "@/lib/scenario";

/**
 * THE INVERSE SURFACE — CONTRACT.md §6b / §6c.
 *
 * The forward panel asks "given this event, what is the distribution?".
 * This asks the inverted question: "for a 75% chance of a move down, what
 * event would it take?".
 *
 * §6c is implemented literally:
 *  - a SLIDER from 50% to 95% is the primary control;
 *  - PRESET BUTTONS at 60 / 75 / 90 exist in both directions;
 *  - direction is green for up and red for down, and ALWAYS paired with a word
 *    and an arrow glyph, because colour is never the only channel (8% of men
 *    are red-green colourblind);
 *  - the ACHIEVED probability is displayed next to the target whenever they
 *    differ, and it is the visually dominant number of the two.
 *
 * The achieved figure is whatever the forward model measured. This component
 * has no code path that can print the target where the achieved belongs.
 */

const UP = "var(--color-pos)";
const DOWN = "var(--color-neg)";
const PRESETS = [60, 75, 90] as const;

export function ScenarioPanel({
  ticker, asOf, horizon, mode,
}: {
  ticker: string;
  asOf: string;
  horizon: number;
  mode: Mode;
}) {
  const [direction, setDirection] = useState<Direction>("down");
  const [target, setTarget] = useState(75);        // whole percent, 50..95
  const [running, setRunning] = useState(false);
  const [res, setRes] = useState<ScenarioResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const accent = direction === "up" ? UP : DOWN;
  const arrow = direction === "up" ? "▲" : "▼";
  const word = direction === "up" ? "Up" : "Down";
  const side = direction === "up" ? "buy side" : "sell side";

  const trackPos = ((target - 50) / 45) * 100;
  const trackFill = `linear-gradient(90deg, ${accent} 0%, ${accent} ${trackPos}%, var(--color-gray-200) ${trackPos}%, var(--color-gray-200) 100%)`;

  const run = useCallback(
    async (forceMock = false) => {
      setRunning(true);
      setErr(null);
      const body = {
        ticker,
        direction,
        target_prob: target / 100,
        as_of_date: asOf,
        horizon_days: horizon,
        n_candidates: 3,
      };
      try {
        const r = forceMock
          ? mockScenario(body)
          : await requestScenario(mode, body);
        setRes(r);
      } catch (e) {
        setRes(null);
        setErr(e instanceof Error ? e.message : String(e));
      } finally {
        setRunning(false);
      }
    },
    [ticker, direction, target, asOf, horizon, mode],
  );

  const best = res?.scenarios?.[0] ?? null;

  return (
    <div className="grid min-w-0 gap-8">
      {/* The property of the problem, stated before any result appears. */}
      <div className="callout px-6 py-5">
        <div className="label" style={{ color: "var(--color-blue)" }}>
          The inverse is not unique
        </div>
        <p className="mt-2 max-w-[86ch] text-[1.0625rem] leading-relaxed text-[var(--color-ink-dim)]">
          Many different events produce the same probability, so what comes back is a{" "}
          <strong className="font-semibold text-[var(--color-navy)]">set of candidates</strong>, never
          &ldquo;the&rdquo; answer. Each candidate&rsquo;s probability is{" "}
          <strong className="font-semibold text-[var(--color-navy)]">computed</strong> by running its
          event text back through the forward model and measuring the fraction of paths that move in
          the requested direction. A language model may draft the words. It never states the number.
        </p>
      </div>

      {/* ---------------- controls ---------------- */}
      <div className="grid min-w-0 gap-8 rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] p-5 sm:p-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="grid gap-6">
          {/* direction */}
          <div>
            <div className="label mb-2" id="dir-label">Direction of the move</div>
            <div className="flex flex-wrap gap-3" role="group" aria-labelledby="dir-label">
              {(["up", "down"] as Direction[]).map((d) => {
                const on = direction === d;
                const c = d === "up" ? UP : DOWN;
                return (
                  <button
                    key={d}
                    onClick={() => setDirection(d)}
                    aria-pressed={on}
                    className="flex items-center gap-2 rounded-full border px-5 py-2.5 text-base font-semibold transition"
                    style={{
                      borderColor: c,
                      background: on ? c : "#fff",
                      color: on ? "#fff" : c,
                    }}
                  >
                    <span aria-hidden="true">{d === "up" ? "▲" : "▼"}</span>
                    <span>{d === "up" ? "Up · buy side" : "Down · sell side"}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* slider — the primary control */}
          <div>
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <label htmlFor="target-prob" className="label">
                Target probability — P({word.toLowerCase()}) over {horizon} sessions
              </label>
              <span className="label">drag to any value, 50% to 95%</span>
            </div>
            <input
              id="target-prob"
              className="prob-slider mt-3"
              type="range"
              min={50}
              max={95}
              step={1}
              value={target}
              onChange={(e) => setTarget(Number(e.target.value))}
              aria-valuetext={`${target} percent probability of a move ${direction}`}
              style={
                {
                  "--slider-accent": accent,
                  "--slider-track": trackFill,
                } as React.CSSProperties
              }
            />
            {/* Ticks are positioned proportionally, not flexed evenly — the
                50→95 range is not uniform in six steps and an evenly spaced
                row would put the 95% mark in the wrong place. */}
            <div className="relative mt-1 h-5">
              {[50, 60, 70, 80, 90, 95].map((t) => (
                <span
                  key={t}
                  className="num absolute text-xs text-[var(--color-ink-faint)]"
                  style={{
                    left: `${((t - 50) / 45) * 100}%`,
                    transform:
                      t === 50 ? "none" : t === 95 ? "translateX(-100%)" : "translateX(-50%)",
                  }}
                >
                  {t}%
                </span>
              ))}
            </div>
          </div>

          {/* presets — 60 / 75 / 90, both directions, per §6c */}
          <div>
            <div className="label mb-2">One-click targets</div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {(["up", "down"] as Direction[]).map((d) =>
                PRESETS.map((p) => {
                  const c = d === "up" ? UP : DOWN;
                  const on = direction === d && target === p;
                  return (
                    <button
                      key={`${d}-${p}`}
                      onClick={() => { setDirection(d); setTarget(p); }}
                      aria-pressed={on}
                      className="flex items-center justify-between gap-2 rounded-lg border px-4 py-3 text-left transition hover:shadow-[var(--shadow-lift)]"
                      style={{
                        borderColor: on ? c : "var(--color-rule)",
                        background: on ? c : "#fff",
                        color: on ? "#fff" : "var(--color-ink)",
                        boxShadow: on ? `0 0 0 1px ${c}` : undefined,
                      }}
                    >
                      <span className="flex items-center gap-2 text-sm font-semibold">
                        <span aria-hidden="true" style={{ color: on ? "#fff" : c }}>
                          {d === "up" ? "▲" : "▼"}
                        </span>
                        {d === "up" ? "Up" : "Down"}
                      </span>
                      <span className="num text-lg font-semibold">{p}%</span>
                    </button>
                  );
                }),
              )}
            </div>
          </div>
        </div>

        {/* readout + run */}
        <div className="flex flex-col justify-between gap-6 rounded-lg border border-[var(--color-rule)] bg-white p-6">
          <div>
            <div className="label">You are asking for</div>
            <div className="mt-3 flex items-center gap-3">
              <span
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-xl"
                style={{ background: accent, color: "#fff" }}
                aria-hidden="true"
              >
                {arrow}
              </span>
              <div>
                <div className="figure text-[2.75rem]" style={{ color: accent }}>{target}%</div>
                <div className="text-sm font-semibold" style={{ color: accent }}>
                  {word} · {side}
                </div>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-[var(--color-ink-faint)]">
              A {target}% chance that {ticker} closes {direction} over the next {horizon} sessions,
              as of{" "}
              <span className="num">{asOf}</span>. Ticker and date follow the selector above.
            </p>
          </div>

          <button onClick={() => void run()} disabled={running} className="btn-primary w-full">
            {running ? "Searching…" : "Find candidate events"}
          </button>
        </div>
      </div>

      {/* ---------------- error ---------------- */}
      {err && (
        <div className="rounded-lg border border-[var(--color-neg)] bg-[#FDF3F2] px-6 py-5">
          <div className="label" style={{ color: "var(--color-neg)" }}>
            scenario endpoint error
          </div>
          <div className="num mt-2 text-sm text-[var(--color-ink-dim)]">{err}</div>
          <p className="mt-3 max-w-[80ch] text-sm leading-relaxed text-[var(--color-ink-dim)]">
            POST /api/scenario did not answer. Nothing is invented to cover for it — the
            synthetic path below is clearly labelled as synthetic and its probabilities are still
            measured off in-browser ensembles rather than asserted.
          </p>
          <button onClick={() => void run(true)} className="btn-secondary mt-4 bg-white">
            Run the synthetic search instead
          </button>
        </div>
      )}

      {/* ---------------- results ---------------- */}
      {res && (
        <div className="grid gap-6">
          <div className="flex flex-wrap items-end justify-between gap-6 border-t border-[var(--color-rule)] pt-6">
            <div>
              <div className="label">Best candidate found</div>
              <div className="mt-2 flex flex-wrap items-end gap-4">
                <span className="figure text-[2.75rem]" style={{ color: accent }}>
                  {best ? pctPlain(best.achieved_prob, 1) : "—"}
                </span>
                <span className="mb-2 text-base text-[var(--color-ink-dim)]">
                  achieved against a{" "}
                  <span className="num font-semibold text-[var(--color-navy)]">
                    {pctPlain(res.target_prob, 1)}
                  </span>{" "}
                  target
                  {best && (
                    <>
                      {" · miss "}
                      <span className="num font-semibold text-[var(--color-navy)]">
                        {(res.best_error * 100).toFixed(1)} pp
                      </span>
                    </>
                  )}
                </span>
              </div>
            </div>
            <div className="flex flex-wrap gap-6">
              <Meta label="Search iterations" value={String(res.search_iterations)} />
              <Meta label="Candidates" value={String(res.scenarios.length)} />
              <Meta
                label="Source"
                value={res.source === "live" ? "backend model" : "synthetic"}
                tone={res.source === "live" ? "var(--color-blue)" : "var(--color-notice)"}
              />
            </div>
          </div>

          {res.source !== "live" && (
            <div className="callout-notice px-5 py-4 text-sm leading-relaxed"
              style={{ color: "var(--color-notice)" }}>
              <span className="font-semibold">Synthetic search.</span> These candidate ensembles were
              generated in-browser by a seeded RNG, not by the backend generator. The probabilities
              are still measured off those paths — nothing here is a stated number — but they are not
              a model result and must not be quoted as one.
            </div>
          )}

          {res.note && (
            <div className="rounded-lg border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-5 py-4">
              <div className="label mb-2">What the search actually did</div>
              <p className="max-w-[104ch] text-sm leading-relaxed text-[var(--color-ink-dim)]">
                {res.note}
              </p>
            </div>
          )}

          <div className="grid gap-5">
            {res.scenarios.map((s, i) => (
              <CandidateCard
                key={i}
                index={i + 1}
                cand={s}
                target={res.target_prob}
                direction={res.direction}
                live={res.source === "live"}
              />
            ))}
          </div>

          {res.scenarios.length === 0 && (
            <p className="text-base text-[var(--color-ink-dim)]">
              The search returned no candidate for this target. That is reported as-is rather than
              padded with a near miss relabelled as a hit.
            </p>
          )}
        </div>
      )}

      {!res && !err && (
        <div className="flex min-h-[140px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-[var(--color-gray-400)] px-6 py-10 text-center">
          <div className="label-title" style={{ color: "var(--color-ink-faint)" }}>
            set a target, then search
          </div>
          <p className="max-w-[62ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
            The slider takes any whole percentage between 50 and 95 — 57% works exactly like 75%.
            Each returned candidate is scored by the forward model before it is shown.
          </p>
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- */

function Meta({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="num mt-1 text-lg font-semibold"
        style={{ color: tone ?? "var(--color-navy)" }}>{value}</div>
    </div>
  );
}

function CandidateCard({
  cand, index, target, direction, live,
}: {
  cand: ScenarioCandidate;
  index: number;
  target: number;
  direction: Direction;
  /** Which engine measured `achieved_prob`. The badge must not let a synthetic
   *  card read as a backend result if this card is screenshotted on its own. */
  live: boolean;
}) {
  const accent = direction === "up" ? UP : DOWN;
  const differs = Math.abs(cand.achieved_prob - target) >= 0.0005;
  const deltaPp = (cand.achieved_prob - target) * 100;

  const q = cand.quantiles;
  const rows = useMemo(
    () => (q ? ([["p5", q.p5], ["p25", q.p25], ["p50", q.p50], ["p75", q.p75], ["p95", q.p95]] as [string, number][]) : []),
    [q],
  );

  return (
    <article className="min-w-0 overflow-hidden rounded-lg border border-[var(--color-rule)] bg-white shadow-[var(--shadow-card)]">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--color-rule)] px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="num rounded-full bg-[var(--color-blue-tint)] px-2 py-0.5 text-xs font-semibold"
            style={{ color: "var(--color-blue)" }}>
            {String(index).padStart(2, "0")}
          </span>
          <span
            className="flex items-center gap-2 rounded-full px-3 py-1 text-sm font-semibold"
            style={{ background: accent, color: "#fff" }}
          >
            <span aria-hidden="true">{direction === "up" ? "▲" : "▼"}</span>
            {direction === "up" ? "Up · buy side" : "Down · sell side"}
          </span>
        </div>
        {cand.verified ? (
          <span className="label" style={{ color: live ? "var(--color-blue)" : "var(--color-notice)" }}>
            {live
              ? "verified · the backend forward model ran on this text"
              : "verified · the in-browser synthetic model ran on this text"}
          </span>
        ) : (
          <span className="label" style={{ color: "var(--color-notice)" }}>
            unverified · no forward model run — treat as a draft, not a result
          </span>
        )}
      </header>

      <div className="grid min-w-0 gap-8 p-5 sm:p-6 lg:grid-cols-[260px_minmax(0,1fr)]">
        {/* the achieved probability dominates; the target sits beside it */}
        <div>
          <div className="label">Achieved · computed</div>
          <div className="figure mt-2 text-[3rem]" style={{ color: accent }}>
            {pctPlain(cand.achieved_prob, 1)}
          </div>
          <div className="mt-3 border-t border-[var(--color-rule)] pt-3">
            <div className="flex items-baseline justify-between gap-3">
              <span className="label">Target asked for</span>
              <span className="num text-lg font-semibold text-[var(--color-ink-dim)]">
                {pctPlain(target, 1)}
              </span>
            </div>
            <div className="mt-1 flex items-baseline justify-between gap-3">
              <span className="label">Difference</span>
              <span className="num text-lg font-semibold"
                style={{ color: differs ? "var(--color-notice)" : "var(--color-blue)" }}>
                {differs
                  ? `${deltaPp >= 0 ? "+" : "−"}${Math.abs(deltaPp).toFixed(1)} pp`
                  : "0.0 pp"}
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-[var(--color-ink-faint)]">
              {differs
                ? "The search could not close the gap entirely. The measured number is reported, not the one that was asked for."
                : "The search closed the gap. The number above is still the measured one."}
            </p>
          </div>
        </div>

        <div className="grid gap-5">
          <div>
            <div className="label mb-2">Candidate event — hypothetical</div>
            <p className="text-[1.0625rem] leading-relaxed text-[var(--color-ink)]">
              {cand.event_text}
            </p>
          </div>

          {rows.length > 0 && (
            <div>
              <div className="label mb-2">Forward return quantiles at the horizon</div>
              <div className="grid grid-cols-2 gap-[1px] overflow-hidden rounded-lg border border-[var(--color-rule)] bg-[var(--color-rule)] sm:grid-cols-3 lg:grid-cols-5">
                {rows.map(([k, v]) => (
                  <div key={k} className="bg-white px-3 py-3">
                    <div className="label">{k}</div>
                    <div className="num mt-1 text-base font-semibold"
                      style={{ color: v < 0 ? "var(--color-neg)" : "var(--color-pos)" }}>
                      {pct(v, 1)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {cand.analogs_used && cand.analogs_used.length > 0 && (
            <div>
              <div className="label mb-2">Analogs the draft was grounded in</div>
              <ul className="flex flex-wrap gap-2">
                {cand.analogs_used.map((a, i) => (
                  <li key={`${a.date}-${i}`}
                    className="rounded-full border border-[var(--color-rule)] bg-[var(--color-panel-2)] px-3 py-1.5 text-sm">
                    <span className="num font-semibold text-[var(--color-navy)]">{a.ticker} {a.date}</span>
                    <span className="num ml-2"
                      style={{ color: a.move_pct < 0 ? "var(--color-neg)" : "var(--color-pos)" }}>
                      {pct(a.move_pct, 1)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {cand.narrative && (
            <p className="border-l-[3px] border-[var(--color-blue)] pl-4 text-sm leading-relaxed text-[var(--color-ink-dim)]">
              {cand.narrative}
            </p>
          )}
        </div>
      </div>
    </article>
  );
}
