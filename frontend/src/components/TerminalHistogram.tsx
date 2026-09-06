"use client";

import { useMemo } from "react";
import type { Ensemble } from "@/lib/types";
import { histogram, pct, terminalReturns } from "@/lib/quant";

/**
 * Terminal cumulative-return distribution at the horizon, with the realized
 * return dropped in as a vertical line. The quantile marks are the same five
 * numbers the fan chart draws, so the two charts are provably the same object.
 *
 * Light ground: bars are --color-blue-light with a 1px white gap between them
 * (DESIGN_AMEX §5); the realized mark is coloured by sign and labelled on the
 * line itself.
 */
export function TerminalHistogram({
  ensemble, actual, height = 260,
}: {
  ensemble: Ensemble;
  actual?: number | null;
  height?: number;
}) {
  const W = 1000;
  const H = height;
  const M = { t: 18, r: 24, b: 46, l: 24 };

  const term = useMemo(() => terminalReturns(ensemble.paths), [ensemble]);

  const { lo, hi, bins, maxN } = useMemo(() => {
    if (term.length === 0) return { lo: -0.1, hi: 0.1, bins: [], maxN: 1 };
    let a = Math.min(...term);
    let b = Math.max(...term);
    if (actual != null) { a = Math.min(a, actual); b = Math.max(b, actual); }
    const p = (b - a) * 0.04;
    a -= p; b += p;
    const bs = histogram(term, 56, a, b);
    return { lo: a, hi: b, bins: bs, maxN: Math.max(1, ...bs.map((x) => x.n)) };
  }, [term, actual]);

  const x = (v: number) => M.l + ((v - lo) / (hi - lo || 1)) * (W - M.l - M.r);
  const barH = (n: number) => (n / maxN) * (H - M.t - M.b);
  // Same 350ms total-stagger budget every chart in this app uses.
  const stagger = 350 / Math.max(1, bins.length);

  const q = ensemble.quantiles;
  const marks: [string, number][] = [
    ["p5", q.p5], ["p25", q.p25], ["p50", q.p50], ["p75", q.p75], ["p95", q.p95],
  ];

  const actualColor =
    actual != null && actual < 0 ? "var(--color-neg)" : "var(--color-pos)";

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
        aria-label="Distribution of terminal returns across the ensemble">
        {/* the axis carries meaning, so it is on the 3:1 token at 2px */}
        <line x1={M.l} x2={W - M.r} y1={H - M.b} y2={H - M.b}
          stroke="var(--color-axis)" strokeWidth={2} />

        {bins.map((b, i) => {
          const w = Math.max(1, x(b.x1) - x(b.x0) - 1.5);
          const h = barH(b.n);
          return (
            <rect key={i} x={x(b.x0)} y={H - M.b - h} width={w} height={h}
              fill="var(--color-blue-light)"
              className="bloom"
              style={{ animationDelay: `${i * stagger}ms` }} />
          );
        })}

        {/* quantile ticks under the axis */}
        {marks.map(([k, v]) => (
          <g key={k}>
            <line x1={x(v)} x2={x(v)} y1={H - M.b} y2={H - M.b + 8}
              stroke="var(--color-navy)" strokeWidth={k === "p50" ? 2.5 : 1.5} />
            <text x={x(v)} y={H - M.b + 24} textAnchor="middle" className="num"
              fontSize="13" fill="var(--color-ink-faint)">{k}</text>
            <text x={x(v)} y={H - M.b + 40} textAnchor="middle" className="num"
              fontSize="13" fill="var(--color-navy)">{pct(v, 0)}</text>
          </g>
        ))}

        {/* zero */}
        {lo < 0 && hi > 0 && (
          <line x1={x(0)} x2={x(0)} y1={M.t} y2={H - M.b}
            stroke="var(--color-axis)" strokeWidth={1.5} strokeDasharray="4 6" />
        )}

        {/* THE ACTUAL — vertical line, labelled on the mark */}
        {actual != null && (
          <g>
            <line x1={x(actual)} x2={x(actual)} y1={M.t - 6} y2={H - M.b + 6}
              stroke={actualColor} strokeWidth={3} />
            <polygon
              points={`${x(actual) - 7},${M.t - 6} ${x(actual) + 7},${M.t - 6} ${x(actual)},${M.t + 6}`}
              fill={actualColor} />
            <text
              x={x(actual) + (x(actual) > W * 0.72 ? -12 : 12)}
              y={M.t + 22}
              textAnchor={x(actual) > W * 0.72 ? "end" : "start"}
              className="num" fontSize="15" fontWeight={600} fill={actualColor}>
              REALIZED {pct(actual)}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
