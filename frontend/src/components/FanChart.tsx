"use client";

import { useMemo } from "react";
import type { Ensemble } from "@/lib/types";
import { buildFan, histogram, pct, terminalReturns } from "@/lib/quant";

/**
 * THE MONEY SHOT.
 * Quantile fan (p5–p95, p25–p75, median) over the forecast horizon, with the
 * realized return laid over it when the as-of date is historical.
 *
 * Light-ground rules (DESIGN_AMEX §5): bands are tints of --color-blue at
 * increasing opacity toward the median; the median is solid navy; the realized
 * return is coloured by SIGN (--pos / --neg) and labelled directly on the line
 * rather than in a legend; nothing is thinner than 2px rendered.
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

  /* Colour of the realized mark follows its SIGN, per DESIGN_AMEX §5. The
     label always carries the signed number as well, so colour is decoration
     on top of a value, never the only channel. */
  const actualColor =
    actual != null && actual < 0 ? "var(--color-neg)" : "var(--color-pos)";

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label="Quantile fan of simulated forward returns">
        <defs>
          {/* Tints of the brand blue, deepening toward the median. The two
              bands stay separable because the outer tops out below where the
              inner starts. */}
          <linearGradient id="fanOuter" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-blue)" stopOpacity="0.10" />
            <stop offset="100%" stopColor="var(--color-blue)" stopOpacity="0.18" />
          </linearGradient>
          <linearGradient id="fanInner" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-blue)" stopOpacity="0.26" />
            <stop offset="100%" stopColor="var(--color-blue)" stopOpacity="0.38" />
          </linearGradient>
        </defs>

        {/* grid. Gridlines sit on --gray-200 and never darker (DESIGN_AMEX §5);
            the zero line carries meaning, so it is on the 3:1 token at 2px. */}
        {ticks.map((t) => {
          const zero = Math.abs(t) < 1e-9;
          return (
            <g key={t}>
              <line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)}
                stroke={zero ? "var(--color-axis)" : "var(--color-gray-200)"}
                strokeWidth={zero ? 2 : 1.5}
                strokeDasharray={zero ? "0" : "3 6"} />
              <text x={M.l - 12} y={y(t) + 5} textAnchor="end"
                className="num" fontSize="13" fill="var(--color-ink-faint)">
                {(t * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}

        {/* x axis */}
        {Array.from({ length: steps + 1 }, (_, i) => i).map((i) => (
          <text key={i} x={x(i)} y={H - M.b + 26} textAnchor="middle"
            className="num" fontSize="13" fill="var(--color-ink-faint)">
            {i === 0 ? "as-of" : `+${i}d`}
          </text>
        ))}

        {/* bands */}
        <g className="bloom">
          <path d={area(fan.p95, fan.p5)} fill="url(#fanOuter)" />
          <path d={area(fan.p75, fan.p25)} fill="url(#fanInner)" />
          <path d={line(fan.p95)} fill="none" stroke="var(--color-blue)" strokeWidth={2} opacity={0.55} />
          <path d={line(fan.p5)} fill="none" stroke="var(--color-blue)" strokeWidth={2} opacity={0.55} />
          <path d={line(fan.p50)} fill="none" stroke="var(--color-navy)" strokeWidth={3} />
        </g>

        {/* terminal density, right edge */}
        <g transform={`translate(${W - M.r + 14},0)`}>
          {dens.map((b, i) => (
            <rect key={i} x={0} y={y(b.x1)} width={Math.max(0.6, b.w)}
              height={Math.max(1, y(b.x0) - y(b.x1) - 1)}
              fill="var(--color-blue-light)" opacity={0.75} />
          ))}
          {/* NB: no `label` class here — that class sets font-size and
              letter-spacing in CSS, which beats the SVG presentation
              attributes and overflows the right margin. Inline style wins. */}
          <text
            x={M.r - 20} y={M.t - 8}
            textAnchor="end"
            fill="var(--color-ink-faint)"
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "13px",
              fontWeight: 600,
              letterSpacing: "0.08em",
            }}
          >
            TERMINAL DENSITY
          </text>
        </g>

        {/* the actual */}
        {actual != null && (
          <g>
            <line x1={M.l} x2={W - M.r + 14 + (M.r - 46)} y1={y(actual)} y2={y(actual)}
              stroke={actualColor} strokeWidth={3} strokeDasharray="10 5" />
            <circle cx={x(steps)} cy={y(actual)} r={6.5} fill={actualColor} />
            <circle cx={x(steps)} cy={y(actual)} r={12}
              fill="none" stroke={actualColor} strokeWidth={2} opacity={0.55} />
            {/* The label sits hard against the left axis, so when the realized
                value lands near a gridline it would otherwise overprint that
                gridline's % label. Opaque backing, sized off the string. */}
            <rect
              x={M.l + 4} y={y(actual) - 26}
              width={`ACTUAL ${pct(actual)}`.length * 9.5 + 12} height={20} rx={3}
              fill="var(--color-panel)" opacity={0.92}
            />
            <text x={M.l + 10} y={y(actual) - 11} className="num" fontSize="15"
              fill={actualColor} fontWeight={600} letterSpacing="0.04em">
              ACTUAL {pct(actual)}
            </text>
          </g>
        )}

        {/* median label */}
        <text x={x(steps) - 8} y={y(fan.p50[fan.p50.length - 1]) - 12} textAnchor="end"
          className="num" fontSize="13" fill="var(--color-navy)">
          p50 {pct(fan.p50[fan.p50.length - 1])}
        </text>
      </svg>

      <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-2 border-t border-[var(--color-rule)] pt-4">
        <Legend swatch="rgba(0,111,207,0.32)" label="p25–p75" />
        <Legend swatch="rgba(0,111,207,0.14)" label="p5–p95" />
        <Legend swatch="var(--color-navy)" label="median" line />
        {actual != null && <Legend swatch={actualColor} label="realized return" line />}
        {actual != null && (
          <span className="label" style={{ color: inside ? "var(--color-blue)" : "var(--color-neg)" }}>
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
        style={{
          background: swatch,
          boxShadow: line ? undefined : "inset 0 0 0 1px rgba(0,111,207,0.55)",
        }}
        className={line ? "block h-[3px] w-6 rounded-full" : "block h-3 w-6 rounded-sm"}
      />
      <span className="label">{label}</span>
    </span>
  );
}
