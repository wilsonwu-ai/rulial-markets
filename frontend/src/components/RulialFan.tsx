"use client";

import { useMemo } from "react";
import { pct } from "@/lib/quant";
import type { BoltzmannLeg, GeneratorResult } from "@/lib/rulial";
import { AXIS_ORDER, levelKey } from "@/lib/rulial";

/**
 * THE RULIAL FAN — one band per generator, 144 of them, overlaid.
 *
 * The contrast IS the finding, so nothing here averages the grid into a single
 * band. Where the rules agree, 144 translucent p5-p95 areas stack into a dark
 * ribbon: a pocket of reducibility. Where they disagree the bands fan apart
 * into pale haze: computational irreducibility, visible without narration.
 * Smoothing that into one band would delete the entire result.
 *
 * Drawn beside it, deliberately NOT in the same visual language, is the single
 * Boltzmann band: navy, dashed outline, no fill, labelled on the line itself.
 * One rule's worth of uncertainty against 144 rules' worth. Keeping both on
 * screen is a contract requirement (§6d) and it is also the only way the
 * comparison reads.
 *
 * PERFORMANCE. 144 filled paths plus 144 dots is ~290 static SVG nodes, which
 * paints fine. What would not be fine is re-rendering all of them on every
 * hover, so the axis highlight is done entirely in CSS: each path carries its
 * four level keys as classes and the only thing React changes is one
 * `data-hl` attribute on the <svg>. See globals.css, "rulial fan".
 *
 * HONESTY. The engine returns terminal quantiles per rule, not a path matrix,
 * so the intermediate envelope is a sqrt(t) expansion of each rule's terminal
 * quantiles — the same treatment FanChart applies, and it says so on screen.
 */

/** Above this many bands we thin the drawn set and SAY SO. The frozen grid is
 *  144, comfortably under, so this normally never fires. */
const MAX_DRAWN = 288;

export interface RulialFanProps {
  per: GeneratorResult[];
  boltzmann: BoltzmannLeg;
  horizon: number;
  /** CSS level key currently highlighted, e.g. "d0". null = show all equally. */
  highlight: string | null;
  height?: number;
}

export function RulialFan({
  per, boltzmann, horizon, highlight, height = 440,
}: RulialFanProps) {
  const W = 1000;
  const H = height;
  const M = { t: 30, r: 150, b: 46, l: 82 };

  /* ---- drawn set. Thinned by a deterministic stride, never by dropping the
     rules that disagree — that would be the exact failure this chart exists
     to prevent. The count actually drawn is printed under the chart. ---- */
  const stride = Math.max(1, Math.ceil(per.length / MAX_DRAWN));
  const drawn = useMemo(
    () => per.filter((_, i) => i % stride === 0),
    [per, stride],
  );

  const dom = useMemo(() => {
    let lo = Math.min(boltzmann.quantiles.p5, ...per.map((g) => g.quantiles.p5));
    let hi = Math.max(boltzmann.quantiles.p95, ...per.map((g) => g.quantiles.p95));
    if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) { lo = -0.1; hi = 0.1; }
    const pad = Math.max((hi - lo) * 0.1, 0.005);
    return { lo: lo - pad, hi: hi + pad };
  }, [per, boltzmann]);

  const Hn = Math.max(1, horizon);
  const x = (t: number) => M.l + (t / Hn) * (W - M.l - M.r);
  const y = (v: number) =>
    M.t + (1 - (v - dom.lo) / (dom.hi - dom.lo)) * (H - M.t - M.b);

  /** sqrt(t) envelope between the as-of point and a terminal quantile. */
  const envelope = (top: number, bot: number) => {
    const up: string[] = [];
    const dn: string[] = [];
    for (let t = 0; t <= Hn; t++) {
      const s = Math.sqrt(t / Hn);
      up.push(`${t === 0 ? "M" : "L"}${x(t).toFixed(1)},${y(top * s).toFixed(1)}`);
    }
    for (let t = Hn; t >= 0; t--) {
      const s = Math.sqrt(t / Hn);
      dn.push(`L${x(t).toFixed(1)},${y(bot * s).toFixed(1)}`);
    }
    return `${up.join("")}${dn.join("")}Z`;
  };
  const ray = (term: number) => {
    const pts: string[] = [];
    for (let t = 0; t <= Hn; t++) {
      const s = Math.sqrt(t / Hn);
      pts.push(`${t === 0 ? "M" : "L"}${x(t).toFixed(1)},${y(term * s).toFixed(1)}`);
    }
    return pts.join("");
  };

  const bands = useMemo(
    () =>
      drawn.map((g, i) => ({
        i,
        d: envelope(g.quantiles.p95, g.quantiles.p5),
        cls: AXIS_ORDER.map((a) => `rf-${levelKey(a, g.rule[a])}`).join(" "),
      })),
    // envelope closes over the scales, which are derived from per/dom/horizon
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [drawn, dom.lo, dom.hi, Hn, H],
  );

  /* ---- right-edge strip: one tick per rule median, packed into rows so
     agreement reads as a pile and disagreement as a smear ---- */
  const swarm = useMemo(() => {
    const x0 = W - M.r + 22;
    const x1 = W - 14;
    const dx = 6;
    const cols = Math.max(1, Math.floor((x1 - x0) / dx));
    const rows = new Map<number, number>();
    return per
      .filter((g) => Number.isFinite(g.median))
      .map((g) => {
        const yy = y(g.median);
        const row = Math.round(yy / 6.5);
        const k = rows.get(row) ?? 0;
        rows.set(row, k + 1);
        return {
          cx: x0 + (k % cols) * dx,
          cy: yy,
          cls: AXIS_ORDER.map((a) => `rf-${levelKey(a, g.rule[a])}`).join(" "),
          key: `${g.rule.analog_selection}|${g.rule.conditioning}|${g.rule.drift_prior}|${g.rule.resampling}`,
        };
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [per, dom.lo, dom.hi, H]);

  const ticks = useMemo(() => {
    const span = dom.hi - dom.lo;
    const raw = span / 5;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((s) => s * mag).find((s) => s >= raw) ?? mag * 10;
    const out: number[] = [];
    for (let v = Math.ceil(dom.lo / step) * step; v <= dom.hi; v += step) out.push(v);
    return out;
  }, [dom.lo, dom.hi]);

  const bTerm = boltzmann.quantiles;
  const medYEnd = y(bTerm.p50);

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="rulial-svg w-full"
        data-hl={highlight ?? undefined}
        role="img"
        aria-label={
          `Rulial fan: ${per.length} overlaid quantile bands, one per generator rule, ` +
          `with the single-rule Boltzmann band drawn over them for comparison.`
        }
      >
        {/* ---- grid. Zero carries meaning, so it is on the 3:1 token at 2px. ---- */}
        {ticks.map((t) => (
          <g key={t}>
            <line
              x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)}
              stroke="var(--color-gray-200)" strokeWidth={1.5} strokeDasharray="3 6"
            />
            <text
              x={M.l - 12} y={y(t) + 5} textAnchor="end"
              className="num" fontSize="13" fill="var(--color-ink-faint)"
            >
              {(t * 100).toFixed(0)}%
            </text>
          </g>
        ))}

        {/* ---- x axis ---- */}
        {Array.from({ length: Hn + 1 }, (_, i) => i).map((i) => (
          <text
            key={i} x={x(i)} y={H - M.b + 26} textAnchor="middle"
            className="num" fontSize="13" fill="var(--color-ink-faint)"
          >
            {i === 0 ? "as-of" : `+${i}d`}
          </text>
        ))}

        {/* =========================================================
            THE 144. One translucent p5-p95 area per generator. No
            averaging, no smoothing, no dropped rules.
            ========================================================= */}
        <g className="bloom">
          {bands.map((b) => (
            <path key={b.i} d={b.d} className={`rband ${b.cls}`} />
          ))}
        </g>

        {/* =========================================================
            THE ONE. Boltzmann, drawn in a different language entirely:
            navy, dashed, unfilled, labelled on the line.
            ========================================================= */}
        <g>
          {/* zero first, ON TOP of the 144 — it carries meaning and must not be
              buried under a stack of translucent fills. */}
          <line x1={M.l} x2={W - M.r} y1={y(0)} y2={y(0)}
            stroke="var(--color-axis)" strokeWidth={2} />

          {/* White halo under each navy stroke. Navy on a saturated blue ribbon
              is legible on a laptop and gone from the back of a room. */}
          {[bTerm.p95, bTerm.p5].map((q, i) => (
            <g key={i}>
              <path d={ray(q)} fill="none" stroke="#fff" strokeWidth={6} opacity={0.75} />
              <path d={ray(q)} fill="none" stroke="var(--color-navy)"
                strokeWidth={2.5} strokeDasharray="9 5" />
            </g>
          ))}
          <path d={ray(bTerm.p50)} fill="none" stroke="#fff" strokeWidth={7.5} opacity={0.8} />
          <path d={ray(bTerm.p50)} fill="none" stroke="var(--color-navy)" strokeWidth={3.5} />

          {/* Labelled directly on the line, INSIDE the plot: the median strip
              owns the right margin and a label there would sit on the dots. */}
          <rect x={x(Hn) - 176} y={medYEnd - 40} width={172} height={32} rx={4}
            fill="var(--color-panel)" opacity={0.93} />
          <text x={x(Hn) - 8} y={medYEnd - 26} textAnchor="end" fill="var(--color-navy)"
            style={{ fontFamily: "var(--font-sans)", fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em" }}>
            BOLTZMANN · 1 RULE
          </text>
          <text x={x(Hn) - 8} y={medYEnd - 13} textAnchor="end" fill="var(--color-ink-dim)"
            className="num" fontSize="12">
            p50 {pct(bTerm.p50)}
          </text>
        </g>

        {/* ---- direct label for the fan itself ---- */}
        <text
          x={M.l + 10} y={M.t - 10} fill="var(--color-blue)"
          style={{ fontFamily: "var(--font-sans)", fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em" }}
        >
          {per.length} RULES · EACH BAND IS ONE GENERATOR
        </text>

        {/* ---- the median strip ---- */}
        <g>
          <line x1={W - M.r + 14} x2={W - M.r + 14} y1={M.t} y2={H - M.b}
            stroke="var(--color-gray-200)" strokeWidth={1.5} />
          <text
            x={W - 18} y={M.t - 10} textAnchor="end" fill="var(--color-ink-faint)"
            style={{ fontFamily: "var(--font-sans)", fontSize: "12px", fontWeight: 600, letterSpacing: "0.08em" }}
          >
            RULE MEDIANS
          </text>
          {swarm.map((s) => (
            <circle key={s.key} cx={s.cx} cy={s.cy} r={2.6} className={`rdot ${s.cls}`} />
          ))}
          {/* the Boltzmann median, marked in the same strip so the two are
              comparable on one axis rather than across two charts */}
          <line x1={W - M.r + 18} x2={W - 14} y1={medYEnd} y2={medYEnd}
            stroke="var(--color-navy)" strokeWidth={2.5} />
        </g>
      </svg>

      {/* ---- legend + the two disclosures that belong to this chart ---- */}
      <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-[var(--color-rule)] pt-4">
        <Legend label={`${drawn.length} rulial bands (p5–p95)`} kind="fan" />
        <Legend label="Boltzmann p5–p95 (single rule)" kind="dash" />
        <Legend label="Boltzmann median" kind="line" />
        <Legend label="one dot = one rule median" kind="dot" />
        <span className="label ml-auto text-right">
          envelope = √t expansion of each rule&rsquo;s terminal quantiles
        </span>
      </div>
      {stride > 1 && (
        <p className="mt-3 text-sm font-semibold text-[var(--color-notice)]">
          Drawing {drawn.length} of {per.length} bands — thinned by a stride of {stride} for
          frame rate. Every rule still contributes to every number on this page; only the ink
          is downsampled.
        </p>
      )}
    </div>
  );
}

function Legend({ label, kind }: { label: string; kind: "fan" | "dash" | "line" | "dot" }) {
  const swatch =
    kind === "fan" ? (
      <span
        className="block h-3 w-7 rounded-sm"
        style={{
          background:
            "linear-gradient(90deg, rgba(0,111,207,0.10), rgba(0,111,207,0.55))",
          boxShadow: "inset 0 0 0 1px rgba(0,111,207,0.45)",
        }}
      />
    ) : kind === "dash" ? (
      <span
        className="block h-0 w-7"
        style={{ borderTop: "2.5px dashed var(--color-navy)" }}
      />
    ) : kind === "line" ? (
      <span className="block h-[3px] w-7 rounded-full" style={{ background: "var(--color-navy)" }} />
    ) : (
      <span className="block h-[7px] w-[7px] rounded-full" style={{ background: "var(--color-blue)" }} />
    );
  return (
    <span className="flex items-center gap-2">
      {swatch}
      <span className="label">{label}</span>
    </span>
  );
}
