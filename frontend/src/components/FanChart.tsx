"use client";

import { useMemo } from "react";
import type { Ensemble } from "@/lib/types";
import { buildFan, histogram, pct, terminalReturns } from "@/lib/quant";

/**
 * THE MONEY SHOT.
 * Quantile fan (p5–p95, p25–p75, median) over the forecast horizon, with the
 * realized return laid over it as a hot line when the as-of date is historical.
 * The right edge carries the terminal density so the fan and the histogram
 * below read as the same object seen from two angles.
 *
 * Honesty note rendered on screen: CONTRACT §5 types `paths` as a flat list of
 * terminal cumulative returns. When that is what arrives, the intermediate
 * envelope is a sqrt(t) expansion of the terminal quantiles, not path data,
 * and the chart says so.
 */
export function FanChart({
  ensemble, actual, height = 380,
}: {
  ensemble: Ensemble;
  actual?: number | null;
  height?: number;
}) {
  const W = 1000;
  const H = height;
  const M = { t: 22, r: 132, b: 42, l: 74 };

  const fan = useMemo(
    () => buildFan(ensemble.paths, ensemble.horizon_days),
    [ensemble],
  );
  const term = useMemo(() => terminalReturns(ensemble.paths), [ensemble]);

  const steps = fan.p50.length - 1;

  const lo0 = Math.min(fan.p5[fan.p5.length - 1], actual ?? Infinity);
  const hi0 = Math.max(fan.p95[fan.p95.length - 1], actual ?? -Infinity);
  const pad = Math.max((hi0 - lo0) * 0.16, 0.01);
  const lo = lo0 - pad;
  const hi = hi0 + pad;

  const x = (i: number) => M.l + (i / Math.max(1, steps)) * (W - M.l - M.r);
  const y = (v: number) => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);

  const area = (a: number[], b: number[]) => {
    const up = a.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
    const dn = [...b].reverse()
      .map((v, i) => `L${x(b.length - 1 - i).toFixed(1)},${y(v).toFixed(1)}`).join("");
    return `${up}${dn}Z`;
  };
  const line = (a: number[]) =>
    a.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");

  // gridlines on round return values
  const ticks = useMemo(() => {
    const span = hi - lo;
    const raw = span / 5;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((s) => s * mag).find((s) => s >= raw) ?? mag * 10;
    const out: number[] = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) out.push(v);
    return out;
  }, [lo, hi]);

  // terminal density strip on the right edge
  const dens = useMemo(() => {
    const bins = histogram(term, 34, lo, hi);
    const max = Math.max(1, ...bins.map((b) => b.n));
    return bins.map((b) => ({ ...b, w: (b.n / max) * (M.r - 46) }));
  }, [term, lo, hi, M.r]);

  const inside =
    actual != null &&
    actual >= fan.p5[fan.p5.length - 1] &&
    actual <= fan.p95[fan.p95.length - 1];

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label="Quantile fan of simulated forward returns">
        <defs>
          <linearGradient id="fanOuter" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-phosphor)" stopOpacity="0.05" />
            <stop offset="100%" stopColor="var(--color-phosphor)" stopOpacity="0.17" />
          </linearGradient>
          <linearGradient id="fanInner" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-phosphor)" stopOpacity="0.13" />
            <stop offset="100%" stopColor="var(--color-phosphor)" stopOpacity="0.36" />
          </linearGradient>
          <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* grid */}
        {ticks.map((t) => (
          <g key={t}>
            <line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)}
              stroke="var(--color-rule)" strokeWidth={1}
              strokeDasharray={Math.abs(t) < 1e-9 ? "0" : "2 5"}
              opacity={Math.abs(t) < 1e-9 ? 0.9 : 0.6} />
            <text x={M.l - 12} y={y(t) + 4} textAnchor="end"
              className="num" fontSize="13" fill="var(--color-ink-faint)">
              {(t * 100).toFixed(0)}%
            </text>
          </g>
        ))}

        {/* x axis */}
        {Array.from({ length: steps + 1 }, (_, i) => i).map((i) => (
          <text key={i} x={x(i)} y={H - M.b + 24} textAnchor="middle"
            className="num" fontSize="12" fill="var(--color-ink-faint)">
            {i === 0 ? "as-of" : `+${i}d`}
          </text>
        ))}

        {/* bands */}
        <g className="bloom">
          <path d={area(fan.p95, fan.p5)} fill="url(#fanOuter)" />
          <path d={area(fan.p75, fan.p25)} fill="url(#fanInner)" />
          <path d={line(fan.p95)} fill="none" stroke="var(--color-phosphor)" strokeWidth={1} opacity={0.45} />
          <path d={line(fan.p5)} fill="none" stroke="var(--color-phosphor)" strokeWidth={1} opacity={0.45} />
          <path d={line(fan.p50)} fill="none" stroke="var(--color-phosphor)" strokeWidth={2.5}
            filter="url(#glow)" />
        </g>

        {/* terminal density, right edge */}
        <g transform={`translate(${W - M.r + 14},0)`}>
          {dens.map((b, i) => (
            <rect key={i} x={0} y={y(b.x1)} width={Math.max(0.6, b.w)}
              height={Math.max(1, y(b.x0) - y(b.x1) - 1)}
              fill="var(--color-phosphor)" opacity={0.34} />
          ))}
          {/* NB: no `label` class here — that class sets font-size/letter-spacing
              in CSS, which beats the SVG presentation attributes and overflows
              the right margin. Inline style wins instead. */}
          <text
            x={M.r - 20} y={M.t - 8}
            textAnchor="end"
            fill="var(--color-ink-faint)"
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              letterSpacing: "0.06em",
            }}
          >
            TERMINAL DENSITY
          </text>
        </g>

        {/* the actual */}
        {actual != null && (
          <g>
            <line x1={M.l} x2={W - M.r + 14 + (M.r - 46)} y1={y(actual)} y2={y(actual)}
              stroke="var(--color-actual)" strokeWidth={2} strokeDasharray="7 4" opacity={0.95} />
            <circle cx={x(steps)} cy={y(actual)} r={6.5}
              fill="var(--color-actual)" filter="url(#glow)" />
            <circle cx={x(steps)} cy={y(actual)} r={12}
              fill="none" stroke="var(--color-actual)" strokeWidth={1} opacity={0.5} />
            <text x={M.l + 8} y={y(actual) - 11} className="num" fontSize="14"
              fill="var(--color-actual)" letterSpacing="0.08em">
              ACTUAL {pct(actual)}
            </text>
          </g>
        )}

        {/* median label */}
        <text x={x(steps) - 8} y={y(fan.p50[fan.p50.length - 1]) - 12} textAnchor="end"
          className="num" fontSize="13" fill="var(--color-phosphor)" opacity={0.9}>
          p50 {pct(fan.p50[fan.p50.length - 1])}
        </text>
      </svg>

      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-[var(--color-rule)] pt-3">
        <Legend swatch="rgba(55,230,207,0.34)" label="p25–p75" />
        <Legend swatch="rgba(55,230,207,0.14)" label="p5–p95" />
        <Legend swatch="var(--color-phosphor)" label="median" line />
        {actual != null && <Legend swatch="var(--color-actual)" label="realized return" line />}
        {actual != null && (
          <span className="label" style={{ color: inside ? "var(--color-phosphor)" : "var(--color-down)" }}>
            {inside ? "actual landed inside the 90% band" : "actual landed OUTSIDE the 90% band"}
          </span>
        )}
        <span className="label ml-auto">
          {fan.interpolated
            ? "envelope = √t expansion of terminal quantiles (model output is terminal returns)"
            : "envelope = per-step quantiles of the path matrix"}
        </span>
      </div>
    </div>
  );
}

function Legend({ swatch, label, line = false }: { swatch: string; label: string; line?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      <span
        style={{ background: swatch }}
        className={line ? "block h-[2px] w-6" : "block h-3 w-6"}
      />
      <span className="label">{label}</span>
    </span>
  );
}
