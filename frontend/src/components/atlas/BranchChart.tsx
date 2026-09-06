"use client";

import { useMemo } from "react";
import type { Ensemble } from "@/lib/types";
import { buildFan, terminalReturns } from "@/lib/quant";
import { DAY_MS, closeAt, seriesAfter, sliceSeries, toMs, tradingToCalendarDays } from "@/lib/atlas";

/**
 * STATE 3 — THE BRANCH.
 *
 * One picture, one claim: what actually happened was ONE path out of two
 * thousand the model considered reachable.
 *
 * So the ensemble is not drawn in its own chart. Real weekly closes come in
 * from the left in solid navy, hit the branch date, and the fan opens out of
 * that exact point — same axes, same units, same line. The realized outcome
 * continues through the fan as a single solid coloured line, labelled where it
 * lands. If those two things were in separate panels the entire argument would
 * be gone.
 *
 * FOUR HONESTY CONSTRAINTS, all visible on the chart:
 *
 *  1. BROKEN AXIS, DECLARED. Six months of history and five trading days of
 *     forecast cannot share one linear scale — the forecast would be a sliver
 *     two pixels wide. The forward zone is expanded and the break is drawn as
 *     a labelled rule, not hidden.
 *  2. THE CLOUD IS THE ACTUAL SAMPLE. Each dot is one simulated path's
 *     terminal return, drawn where the model put it. It is not a rendering of
 *     the quantiles; the quantiles are a rendering of it.
 *  3. NO INVENTED INTERIOR. CONTRACT §5 gives terminal returns, not a path
 *     matrix, so the envelope between the branch and the horizon is a sqrt(t)
 *     expansion of the terminal quantiles and the caption says so. For the same
 *     reason the realized line is drawn as one straight segment to the close we
 *     actually know: we do not own the intraday path and will not draw one.
 *  4. THE TAIL IS REAL AND SEPARATE. "What came next" is real weekly closes
 *     past the model horizon, behind a toggle, drawn after a labelled divider
 *     so it is never mistaken for forecast.
 */

const W = 1200;
const H = 470;
const M = { t: 34, r: 176, b: 52, l: 84 };
const SPLIT_FRAC = 0.5;

export interface BranchChartProps {
  series: [string, number][];
  branchDate: string;
  horizonDays: number;
  ensemble: Ensemble | null;
  /** realized cumulative return over the horizon, when the outcome is known */
  actual: number | null;
  showTail: boolean;
  /** "all" keeps every real close in frame; "futures" scales to the forecast
   *  so the fan is readable; "auto" picks "futures" when history would squash
   *  it flat. Whichever is active is stated on the chart. */
  fit?: "auto" | "all" | "futures";
  historyWeeks?: number;
  tailWeeks?: number;
}

export function BranchChart({
  series, branchDate, horizonDays, ensemble, actual,
  showTail, fit = "auto", historyWeeks = 26, tailWeeks = 26,
}: BranchChartProps) {
  const branchMs = toMs(branchDate);
  const branchPrice = closeAt(series, branchMs);

  const fwdCalDays = tradingToCalendarDays(horizonDays);
  const zoneCalDays = showTail ? Math.max(fwdCalDays, tailWeeks * 7) : fwdCalDays;

  /* `sliceSeries` deliberately returns one point past each edge so a line
     entering the viewport is drawn to it. Here that is wrong: the extra point
     is the FIRST CLOSE AFTER the branch, and drawing it made the history line
     dive across the branch rule — the one place on this chart where "before"
     and "after" must not touch. Trim it. */
  const hist = useMemo(
    () => sliceSeries(series, branchMs - historyWeeks * 7 * DAY_MS, branchMs)
      .filter((p) => p.ms <= branchMs),
    [series, branchMs, historyWeeks],
  );
  const tail = useMemo(
    () => (branchPrice ? seriesAfter(series, branchMs, zoneCalDays * DAY_MS) : []),
    [series, branchMs, zoneCalDays, branchPrice],
  );

  const fan = useMemo(
    () => (ensemble ? buildFan(ensemble.paths, ensemble.horizon_days) : null),
    [ensemble],
  );
  const term = useMemo(
    () => (ensemble ? terminalReturns(ensemble.paths) : []),
    [ensemble],
  );

  const xSplit = M.l + SPLIT_FRAC * (W - M.l - M.r);

  /** history: calendar ms -> px, left zone */
  const xh = (ms: number) => {
    const lo = branchMs - historyWeeks * 7 * DAY_MS;
    return M.l + ((ms - lo) / Math.max(1, branchMs - lo)) * (xSplit - M.l);
  };
  /** forward: calendar ms -> px, right zone (expanded) */
  const xf = (ms: number) =>
    xSplit + ((ms - branchMs) / Math.max(1, zoneCalDays * DAY_MS)) * (W - M.r - xSplit);
  /** forward: trading-day step 0..H -> px */
  const xs = (step: number) =>
    xf(branchMs + (tradingToCalendarDays(Math.max(0, step)) - (step === 0 ? 1 : 0)) * DAY_MS);

  const xHorizon = xf(branchMs + fwdCalDays * DAY_MS);

  /* ---- y domain ----
     Two candidate frames, because they answer different questions and one of
     them is frequently unreadable. "all" holds every real close in view, which
     is the right picture for BA into March 2020 and the wrong one for the fan:
     a 4x price range squashes a ±12% forecast into a smear. "futures" scales
     to the forecast and lets the history line run off the top, marked where it
     exits. `auto` picks the second when the first would squash the fan by more
     than 4x, and the header says which is live so the frame is never a silent
     choice made on the viewer's behalf. ---- */
  const frames = useMemo(() => {
    const fwd: number[] = [];
    const hist2: number[] = [];
    for (const p of hist) hist2.push(p.v);
    if (branchPrice) {
      fwd.push(branchPrice);
      if (fan) {
        fwd.push(branchPrice * (1 + fan.p5[fan.p5.length - 1]));
        fwd.push(branchPrice * (1 + fan.p95[fan.p95.length - 1]));
        if (term.length) {
          fwd.push(branchPrice * (1 + Math.min(...term)));
          fwd.push(branchPrice * (1 + Math.max(...term)));
        }
      }
      if (actual != null) fwd.push(branchPrice * (1 + actual));
    }
    if (showTail) for (const p of tail) fwd.push(p.v);

    const bound = (vals: number[]) => {
      const clean = vals.filter((v) => Number.isFinite(v) && v > 0);
      if (!clean.length) return { lo: 1, hi: 2 };
      let lo = Math.min(...clean);
      let hi = Math.max(...clean);
      const pad = Math.max((hi - lo) * 0.14, hi * 0.012);
      lo -= pad; hi += pad;
      if (lo <= 0) lo = Math.min(...clean) * 0.9;
      return { lo, hi };
    };
    return { futures: bound(fwd), all: bound([...fwd, ...hist2]) };
  }, [hist, tail, fan, term, actual, branchPrice, showTail]);

  const squash =
    (frames.all.hi - frames.all.lo) / Math.max(1e-9, frames.futures.hi - frames.futures.lo);
  const activeFit: "all" | "futures" =
    fit === "auto" ? (squash > 4 ? "futures" : "all") : fit;
  const dom = activeFit === "futures" ? frames.futures : frames.all;

  const y = (v: number) =>
    M.t + (1 - (v - dom.lo) / Math.max(1e-9, dom.hi - dom.lo)) * (H - M.t - M.b);

  const priceTicks = useMemo(() => {
    const span = dom.hi - dom.lo;
    const raw = span / 4;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((s) => s * mag).find((s) => s >= raw) ?? mag * 10;
    const out: number[] = [];
    for (let v = Math.ceil(dom.lo / step) * step; v <= dom.hi; v += step) out.push(v);
    return out;
  }, [dom]);

  /* Deterministic jitter — a fixed hash, so the cloud does not reshuffle on
     every re-render and the picture is stable while someone talks over it.
     Computed before the early return so the hook order never depends on
     whether we happen to have a price on the branch date. */
  const cloud = useMemo(() => {
    if (!term.length || !branchPrice) return [] as { cx: number; cy: number }[];
    const MAXD = 700;
    const stride = Math.max(1, Math.ceil(term.length / MAXD));
    const yy = (v: number) =>
      M.t + (1 - (v - dom.lo) / Math.max(1e-9, dom.hi - dom.lo)) * (H - M.t - M.b);
    const out: { cx: number; cy: number }[] = [];
    for (let i = 0; i < term.length; i += stride) {
      const h = Math.imul(i + 1, 2654435761) >>> 0;
      const j = (h % 10000) / 10000;
      out.push({ cx: xHorizon + 10 + j * 118, cy: yy(branchPrice * (1 + term[i])) });
    }
    return out;
  }, [term, xHorizon, dom.lo, dom.hi, branchPrice]);

  if (!branchPrice) {
    return (
      <div className="flex min-h-[240px] items-center justify-center rounded-lg border border-dashed border-[var(--color-gray-400)] px-6 py-10 text-center">
        <p className="max-w-[54ch] text-[var(--color-ink-faint)]">
          No close on or before {branchDate} in the bundled price history for this ticker, so there
          is no real line to branch from. Nothing is drawn rather than a line starting at an
          invented level.
        </p>
      </div>
    );
  }

  const bp = branchPrice;
  const P = (r: number) => bp * (1 + r);
  const offScale = hist.filter((p) => p.v > dom.hi || p.v < dom.lo).length;
  const LABEL_W = 200;
  const labelX = Math.max(M.l + 4, Math.min(xHorizon - 8, W - 6 - LABEL_W));

  const fanPath = (arr: number[]) =>
    arr.map((r, i) => `${i === 0 ? "M" : "L"}${xs(i).toFixed(1)},${y(P(r)).toFixed(1)}`).join("");
  const fanArea = (hiArr: number[], loArr: number[]) => {
    const up = hiArr.map((r, i) => `${i === 0 ? "M" : "L"}${xs(i).toFixed(1)},${y(P(r)).toFixed(1)}`).join("");
    const dn = [...loArr].reverse()
      .map((r, i) => `L${xs(loArr.length - 1 - i).toFixed(1)},${y(P(r)).toFixed(1)}`).join("");
    return `${up}${dn}Z`;
  };

  const actColor = actual != null && actual < 0 ? "var(--color-neg)" : "var(--color-pos)";
  const inBand =
    actual != null && fan
      ? actual >= fan.p5[fan.p5.length - 1] && actual <= fan.p95[fan.p95.length - 1]
      : null;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label={`Weekly closes into ${branchDate}, then the ensemble of forward paths and the outcome that happened.`}>

        {/* price gridlines */}
        {priceTicks.map((t) => (
          <g key={t}>
            <line x1={M.l} x2={W - M.r + 130} y1={y(t)} y2={y(t)}
              stroke="var(--color-gray-200)" strokeWidth={1.5} strokeDasharray="3 6" />
            <text x={M.l - 12} y={y(t) + 5} textAnchor="end" fill="var(--color-ink-faint)"
              style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontVariantNumeric: "tabular-nums" }}>
              ${t >= 100 ? t.toFixed(0) : t.toFixed(2)}
            </text>
          </g>
        ))}

        {/* the branch price level, running the width of the chart */}
        <line x1={M.l} x2={W - M.r + 130} y1={y(bp)} y2={y(bp)}
          stroke="var(--color-axis)" strokeWidth={2} />

        {/* ---- forward zone ground + the declared axis break ---- */}
        <rect x={xSplit} y={M.t - 10} width={W - M.r - xSplit} height={H - M.t - M.b + 20}
          fill="var(--color-blue-tint)" opacity={0.55} />
        <line x1={xSplit} x2={xSplit} y1={M.t - 14} y2={H - M.b + 10}
          stroke="var(--color-blue)" strokeWidth={2.5} />
        <text x={xSplit - 10} y={M.t - 18} textAnchor="end" fill="var(--color-navy)"
          style={{ fontFamily: "var(--font-mono)", fontSize: 14, fontWeight: 700 }}>
          {branchDate}
        </text>
        <text x={xSplit + 10} y={M.t - 18} fill="var(--color-blue)"
          style={{ fontFamily: "var(--font-sans)", fontSize: 12, fontWeight: 600, letterSpacing: "0.08em" }}>
          FORWARD — AXIS EXPANDED
        </text>

        {/* ---- what actually happened, past the horizon (real, toggled) ---- */}
        {showTail && tail.length > 1 && (
          <>
            <line x1={xHorizon} x2={xHorizon} y1={M.t - 4} y2={H - M.b + 6}
              stroke="var(--color-axis)" strokeWidth={2} strokeDasharray="6 5" />
            <text x={xHorizon + 6} y={H - M.b + 34} fill="var(--color-ink-faint)"
              style={{ fontFamily: "var(--font-sans)", fontSize: 12, fontWeight: 600, letterSpacing: "0.06em" }}>
              HORIZON ENDS · REAL CLOSES BEYOND
            </text>
            <path
              d={[{ ms: branchMs, v: bp }, ...tail]
                .map((p, i) => `${i === 0 ? "M" : "L"}${xf(p.ms).toFixed(1)},${y(p.v).toFixed(1)}`)
                .join("")}
              fill="none" stroke="var(--color-navy)" strokeWidth={2.5}
              opacity={0.42} strokeLinejoin="round" />
          </>
        )}

        {/* ---- the ensemble ---- */}
        {fan && (
          <g className="bloom">
            <path d={fanArea(fan.p95, fan.p5)} fill="var(--color-blue)" fillOpacity={0.14} />
            <path d={fanArea(fan.p75, fan.p25)} fill="var(--color-blue)" fillOpacity={0.3} />
            <path d={fanPath(fan.p95)} fill="none" stroke="var(--color-blue)" strokeWidth={2} opacity={0.7} />
            <path d={fanPath(fan.p5)} fill="none" stroke="var(--color-blue)" strokeWidth={2} opacity={0.7} />
            <path d={fanPath(fan.p50)} fill="none" stroke="var(--color-navy)" strokeWidth={2.5} strokeDasharray="8 6" />
          </g>
        )}

        {/* ---- the sampled futures ---- */}
        {cloud.map((c, i) => (
          <circle key={i} cx={c.cx} cy={c.cy} r={2.1} fill="var(--color-blue)" fillOpacity={0.17} />
        ))}
        {cloud.length > 0 && (
          /* right-anchored: at horizon = right edge (the no-tail case) a
             left-anchored label runs off the viewBox and loses its last word */
          <text x={W - 6} y={M.t - 6} textAnchor="end" fill="var(--color-blue)"
            style={{ fontFamily: "var(--font-sans)", fontSize: 12, fontWeight: 600, letterSpacing: "0.08em" }}>
            {term.length.toLocaleString()} SAMPLED FUTURES
          </text>
        )}

        {/* ---- the real line coming in ---- */}
        <clipPath id="branch-plot">
          <rect x={M.l - 2} y={M.t - 12} width={W - M.r - M.l + 134} height={H - M.t - M.b + 24} />
        </clipPath>
        <g clipPath="url(#branch-plot)">
          <path
            d={[...hist, { ms: branchMs, v: bp }]
              .map((p, i) => `${i === 0 ? "M" : "L"}${xh(p.ms).toFixed(1)},${y(p.v).toFixed(1)}`)
              .join("")}
            fill="none" stroke="var(--color-navy)" strokeWidth={3}
            strokeLinejoin="round" strokeLinecap="round" />
        </g>
        {offScale > 0 && (
          <text x={M.l + 4} y={M.t + 12} fill="var(--color-navy)"
            style={{ fontFamily: "var(--font-sans)", fontSize: 12, fontWeight: 700 }}>
            ↑ {offScale} earlier close{offScale === 1 ? "" : "s"} above this frame
          </text>
        )}
        <text x={M.l + 4} y={M.t - 18} fill="var(--color-navy)"
          style={{ fontFamily: "var(--font-sans)", fontSize: 12, fontWeight: 600, letterSpacing: "0.08em" }}>
          {historyWeeks} WEEKS OF REAL CLOSES
        </text>

        {/* ---- the one that happened ---- */}
        {actual != null && (
          <g>
            <path
              d={`M${xSplit.toFixed(1)},${y(bp).toFixed(1)}L${xHorizon.toFixed(1)},${y(P(actual)).toFixed(1)}`}
              fill="none" stroke={actColor} strokeWidth={4} strokeLinecap="round" />
            <circle cx={xHorizon} cy={y(P(actual))} r={9} fill="var(--color-panel)" />
            <circle cx={xHorizon} cy={y(P(actual))} r={6.5} fill={actColor} />
            {/* Direct label, per DESIGN_AMEX §5 — never make the viewer hunt a
                legend for the single most important mark. Clamped inside the
                viewBox: with the tail off the horizon IS the right edge, and
                an unclamped 200px plate loses its own number off the side. */}
            <rect
              x={labelX} y={y(P(actual)) + (actual < 0 ? 14 : -38)}
              width={LABEL_W} height={26} rx={4}
              fill="var(--color-panel)" stroke={actColor} strokeWidth={2} />
            <text
              x={labelX + 10} y={y(P(actual)) + (actual < 0 ? 32 : -20)}
              fill={actColor}
              style={{ fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 700, letterSpacing: "0.02em" }}>
              WHAT HAPPENED {actual >= 0 ? "+" : "−"}{(Math.abs(actual) * 100).toFixed(1)}%
            </text>
          </g>
        )}

        {/* branch anchor */}
        <circle cx={xSplit} cy={y(bp)} r={6} fill="var(--color-navy)" />
        <circle cx={xSplit} cy={y(bp)} r={11} fill="none" stroke="var(--color-navy)" strokeWidth={2} opacity={0.5} />

        {/* Forward axis. With the tail on, the horizon is 4% of the zone and
            "+1d…+5d" collapse into an unreadable stack, so the labels become
            calendar months instead. Same axis, honest labels for its width. */}
        {showTail
          ? [0, 0.25, 0.5, 0.75, 1].map((f) => {
              const ms = branchMs + f * zoneCalDays * DAY_MS;
              return (
                <text key={f} x={xf(ms)} y={H - M.b + 24}
                  textAnchor={f === 0 ? "start" : f === 1 ? "end" : "middle"}
                  fill="var(--color-ink-faint)"
                  style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontVariantNumeric: "tabular-nums" }}>
                  {new Date(ms).toISOString().slice(0, 7)}
                </text>
              );
            })
          : fan && Array.from({ length: Math.min(horizonDays, 10) + 1 }, (_, i) =>
              Math.round((i * horizonDays) / Math.min(horizonDays, 10)),
            ).filter((v, i, a) => a.indexOf(v) === i).map((step) => (
              <text key={step} x={xs(step)} y={H - M.b + 24} textAnchor="middle"
                fill="var(--color-ink-faint)"
                style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontVariantNumeric: "tabular-nums" }}>
                {step === 0 ? "0" : `+${step}d`}
              </text>
            ))}

        <line x1={M.l} x2={W - M.r + 130} y1={H - M.b + 6} y2={H - M.b + 6}
          stroke="var(--color-axis)" strokeWidth={2} />
      </svg>

      <div className="mt-4 flex flex-wrap items-center gap-x-7 gap-y-2 border-t border-[var(--color-rule)] pt-4">
        <Legend swatch="var(--color-navy)" label="real closes" line />
        {fan && <Legend swatch="rgba(0,111,207,0.30)" label="middle half of futures" />}
        {fan && <Legend swatch="rgba(0,111,207,0.14)" label="90% of futures" />}
        {fan && <Legend swatch="var(--color-navy)" label="model median" dashed />}
        {actual != null && <Legend swatch={actColor} label="what happened" line />}
        {inBand != null && (
          <span className="label" style={{ color: inBand ? "var(--color-blue)" : "var(--color-neg)" }}>
            {inBand ? "the outcome landed inside the 90% band" : "the outcome landed OUTSIDE the 90% band"}
          </span>
        )}
      </div>
      <p className="mt-3 max-w-[110ch] text-sm leading-relaxed text-[var(--color-ink-faint)]">
        {activeFit === "futures"
          ? "Vertical scale is fitted to the forecast, so the fan is readable; earlier closes can run off the frame and are marked where they do. "
          : "Vertical scale holds every real close in frame. "}
        {fan?.interpolated
          ? "The model returns end-of-horizon outcomes, so the shape between the branch and the horizon is a √t expansion of the terminal quantiles, not path data — and the realized line is one straight segment to the close we actually know."
          : "Per-step quantiles of the returned path matrix."}
      </p>
    </div>
  );
}

function Legend({
  swatch, label, line = false, dashed = false,
}: { swatch: string; label: string; line?: boolean; dashed?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      {line || dashed ? (
        <svg width="26" height="8" aria-hidden>
          <line x1="1" y1="4" x2="25" y2="4" stroke={swatch} strokeWidth={3}
            strokeDasharray={dashed ? "6 4" : undefined} strokeLinecap="round" />
        </svg>
      ) : (
        <span className="block h-3 w-6 rounded-sm"
          style={{ background: swatch, boxShadow: "inset 0 0 0 1px rgba(0,111,207,0.55)" }} />
      )}
      <span className="label">{label}</span>
    </span>
  );
}
